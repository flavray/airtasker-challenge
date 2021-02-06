class RateLimiter:
    """
    RateLimiter allows to guard access to any resource by limiting the number
    of permits allowed for any given requestor for a period of time.

    Any requestor will have limited access, independently from any other
    requestor.
    """

    def __init__(self, permits: int, period_s: int) -> None:
        """
        Create a new RateLimiter with the given amount of `permits` allowed
        over the given `period_s` (seconds).

        If `permits` is <= 1, access will always be allowed.

        :param permits: the number of calls that can be made over a period of time.
        :param period_s: the duration (in seconds) of a period.
        """
        self.permits: int = permits
        self.period_s: int = period_s

        # TODO: actually implement a decent logic
        self.count: int = 0

    def try_acquire(self, requestor: str) -> int:
        """
        Attempt to acquire a permit in the RateLimiter, for a given `requestor`.

        :param requestor: an identifier for a requestor.
        :returns: the number of seconds to wait until the next permit (0 if permit was allowed).
        """
        # TODO: actually implement a decent logic
        self.count += 1
        if self.count > self.permits:
            return 1
        else:
            return 0
