from collections import defaultdict
from typing import Dict
from typing import List
import logging

import pylibmc  # type: ignore


class Store:
    """
    A counter store, that can be incremented and queried.

    NOTE: This class is only used as a trait.
    MemoryStore or MemcacheStore should be used.
    """

    def get_multi(self, keys: List[str]) -> Dict[str, int]:
        raise NotImplemented

    def incr_and_get(self, key: str, ttl_s: int = 0) -> int:
        raise NotImplemented

    def decr(self, key: str) -> None:
        raise NotImplemented


class MemcacheStore(Store):
    """
    A memcache-backed implementation of a counter store.

    Each operation in memcache is atomic, this ensures that the view of the
    state that any client sees is the current view. Counters in previous
    buckets will not change.

    If two clients try to acquire a permit for the same key, they will each get
    a different value, and different rate limits can apply. No race conditions.
    """

    def __init__(self, connection_string: str) -> None:
        """
        Create a new MemcacheStore instance, connecting via the given
        `connection_string`.
        """
        self.log: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.client: pylibmc.Client = pylibmc.Client(
            [connection_string],
            binary=True,
        )

    def get_multi(self, keys: List[str]) -> Dict[str, int]:
        """
        Return the value in memcache for all the given `keys`.

        Each key that exists in memcache is returned. Each key is mapped to its
        corresponding value in the output.

        Returns an empty dictionary if any issue with memcache occurred.

        :param keys: the list of keys to retrieve
        :returns: a mapping key -> value in memcache. Keys not in memcached are not returned.
        """
        try:
            return self.client.get_multi(keys)
        except pylibmc.Error:
            self.log.exception("Error getting keys, falling back to empty set")
            return {}

    def incr_and_get(self, key: str, ttl_s: int = 0) -> int:
        """
        Increments and returns the counter corresponding to the given key.

        If the key does not yet exist, it will be created (with value 0) first.

        Time-to-live (TTL) can be configured at key creation: if the key already exists,
        `ttl_s` will be ignored. Default TTL: 0 (do not expire)

        Returns 0 if any issue with memcache occurred.

        :param key: the key to retrieve, created if does not yet exist.
        :param ttl_s: an optional TTL (in seconds) for the key, if it does not yet exist.
        :return: the new value of the key.
        """
        try:
            # use `add` to touch the key and make sure it exists
            # memcache operations are atomic, this ensures the key will only be added by one client
            self.client.add(key, 0, time=ttl_s)
            return self.client.incr(key)
        except pylibmc.Error:
            self.log.exception(f"Error incrementing key: '{key}', assuming null")
            return 0

    def decr(self, key: str) -> None:
        try:
            self.client.decr(key)
        except pylibmc.Error:
            self.log.exception(f"Error decrementing key: '{key}'")


class MemoryStore(Store):
    """
    An in-memory counter store.

    Only used for testing.
    Key expiration is not supported.
    """

    def __init__(self):
        self.counts: Dict[str, int] = defaultdict(int)

    def get_multi(self, keys: List[str]) -> Dict[str, int]:
        return {key: self.counts[key] for key in keys if key in self.counts}

    def incr_and_get(self, key: str, ttl_s: int = 0) -> int:
        self.counts[key] += 1
        return self.counts[key]

    def decr(self, key: str) -> None:
        if key in self.counts:
            self.counts[key] -= 1
