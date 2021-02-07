import time
from typing import Dict
from typing import List
from typing import Optional

from .store import Store


class RateLimiter:
    """
    RateLimiter allows to guard access to any resource by limiting the number
    of permits allowed for any given requestor for a period of time.

    Any requestor will have limited access, independently from any other
    requestor.

    The RateLimiter works by bucketing requests into 1 second-long buckets (all
    the requests in the same second end up in the same bucket).
    Every new attempt to acquire a new permit will look back to all the buckets
    in the period from the current time, one for every second
    (e.g: period = 3,600s --> look back last 3,600 buckets)

    Should the RateLimiter be really popular, buckets could be made larger
    (e.g: 10 seconds, 1 minute, ...). This would lower the memory footprint and
    improve performance, at the expense of precision (the number of seconds to
    wait before successfully acquiring a new permit would only be
    approximated).
    Changing the implementation of `RateLimiter::_store_key`,
    `RateLimiter::_previous_store_keys` and `RateLimiter::_cooldown_period_s`
    to take bucket duration into account would be sufficient.

    Buckets are accessed via a `Store` implementation, which can be anything
    that can atomically hold counters (memory, memcache, Redis, SQL, etc...).

    The RateLimiter discards/revokes attempts to acquire the rate limiter when
    over the limit. This means that there is no negative effect for requestors
    to attempt to acquire the rate-limiter even if they are already out of
    permits.
    """

    def __init__(self, permits: int, period_s: int, store: Store) -> None:
        """
        Create a new RateLimiter with the given amount of `permits` allowed
        over the given `period_s` (seconds).

        If `permits` is < 1, access will always be allowed.

        :param permits: the number of calls that can be made over a period of time.
        :param period_s: the duration (in seconds) of a period.
        """
        self.permits: int = permits
        self.period_s: int = period_s
        self.store: Store = store

    def try_acquire(self, requestor: str) -> int:
        """
        Attempt to acquire a permit in the RateLimiter, for a given `requestor`.

        :param requestor: an identifier for a requestor.
        :returns: the number of seconds to wait until the next permit (0 if permit was allowed).
        """
        if self.permits < 1:
            return 0

        now_s: int = int(time.time())

        current_permits: int = self._current_permits(requestor, now_s)
        previous_permits: Dict[int, int] = self._previous_permits(
            requestor,
            now_s,
        )

        total_permits: int = current_permits + sum(previous_permits.values())

        if total_permits <= self.permits:
            return 0
        else:
            self._revoke_permit(requestor, now_s)
            cooldown_s: int = self._cooldown_period_s(now_s, previous_permits)
            return cooldown_s

    def _current_permits(self, requestor: str, now_s: int) -> int:
        """
        Return the number of permits allowed in the current time bucket, for a
        given requestor.

        This method is stateful, as it increments the number of permits in the
        current bucket (effectively attempting to acquire a new permit).

        :param requestor: an identifier for a requestor.
        :param now_s: the current time, in seconds since epoch.
        :returns: the permit count in the current bucket (+ 1 to include the new permit).
        """
        current_key: str = self._store_key(requestor, now_s)
        return self.store.incr_and_get(current_key, ttl_s=self.period_s)

    def _previous_permits(self, requestor: str, now_s: int) -> Dict[int, int]:
        """
        Return the number of permits allowed for the previous time buckets in
        the configured period of time.

        For each bucket in the time window ([now - period; now]), query the
        counter store for the number of permits that were allowed in the bucket.

        The current bucket is not queried, it is instead done as part of
        `RateLimiter::_current_permits`.

        NOTE: Only returns buckets where a counter is present in the store.

        :param requestor: an identifier for a requestor.
        :param now_s: the current time, in seconds since epoch.
        :returns: the permit count for each bucket used (>0 permits) in the configured period.
        """
        previous_keys: Dict[int, str] = self._previous_store_keys(requestor, now_s)

        permits_in_store: Dict[str, int] = self.store.get_multi(
            keys=list(previous_keys.values()),
        )

        # The store only works with keys, make sure to map these keys back to
        # their timestamps
        return {
            time_s: permits_in_store[key]
            for time_s, key in previous_keys.items()
            if key in permits_in_store
        }

    def _revoke_permit(self, requestor: str, now_s: int) -> None:
        """
        Revoke the last-acquired permit for a given `requestor`.

        Decrement the count for the current key to avoid counting non-permits
        towards the cooldown period.

        As the rate-limiter is "optimistic", permits are first acquired (in
        order to have an up-to-date view of counts). In case the rate-limit was
        exceeded, revert the permit and make sure it is not counted towards
        future uses of the rate limiter.

        :param requestor: an identifier for a requestor.
        :param now_s: the current time, in seconds since epoch.
        """
        current_key: str = self._store_key(requestor, now_s)
        self.store.decr(key=current_key)

    def _cooldown_period_s(
        self,
        now_s: int,
        previous_permits: Dict[int, int],
    ) -> int:
        """
        Compute the cooldown period, the number of seconds to wait until the
        rate limiter can successfully be acquired again.

        The rate-limiter revokes permits that have not been allowed. This means
        that finding the time of the first permit is the only thing required to
        find the cooldown period.

        This method assumes that acquisition of the rate limiter was refused
        before being called.

        :param now_s: the current time, in seconds since epoch.
        :param previous_permits: a mapping of bucket time -> permits. Used to
                                 measure how long permits will need to expire.
        """
        period_start_s: int = now_s - self.period_s

        # The age (seconds) of the earliest/oldest permit. This permit needs to
        # expire before any other permit can be acquired.
        oldest_permit_s: int = now_s

        # Look at every window (second) over the period, in ascending order,
        # and figure out the earliest time a permit was allowed.
        # Each second where no permit was given is a second a requestor will
        # have to wait before acquiring again.
        for previous_time_s in range(period_start_s, now_s):
            permits: int = previous_permits.get(previous_time_s, 0)
            if permits > 0:
                oldest_permit_s = previous_time_s
                break

        return oldest_permit_s - period_start_s

    def _previous_store_keys(self, requestor: str, now_s: int) -> Dict[int, str]:
        """
        Return the keys used to query the counter store for the buckets in the
        configured time period, for a given requestor.

        NOTE: The current bucket is not returned, only previous valid buckets
        in the time period. See `RateLimiter::_current_permits`.

        :param requestor: an identifier for a requestor.
        :param now_s: the current time, in seconds since epoch.
        :returns: the key in the counter store for each bucket in the configured period.
        """
        period_start_s: int = now_s - self.period_s

        return {
            time_s: self._store_key(requestor, time_s)
            for time_s in range(period_start_s, now_s)
        }

    def _store_key(self, requestor: str, time_s: int) -> str:
        """
        Return the key used to query the counter store for a given requestor
        and timestamp.

        :param requestor: an identifier for a requestor.
        :param time_s: a timestamp, in seconds since epoch.
        :returns: a string representation to be used by the counter store.
        """
        return f"{requestor}-{time_s}"
