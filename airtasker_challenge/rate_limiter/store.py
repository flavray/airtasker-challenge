from collections import defaultdict
from typing import Dict
from typing import List
import logging

import pylibmc


class Store:
    """
    A counter store, that can be incremented and queried.

    NOTE: This class is only used as a trait.
    MemoryStore or MemcacheStore should be used.
    """

    def get_multi(self, keys: List[str]) -> Dict[str, int]:
        raise NotImplemented()

    def incr_and_get(self, key: str) -> int:
        raise NotImplemented()


class MemoryStore(Store):
    """
    An in-memory counter store.
    """

    def __init__(self):
        self.counts: Dict[str, int] = defaultdict(int)

    def get_multi(self, keys: List[str]) -> Dict[str, int]:
        return {key: self.counts[key] for key in keys if key in self.counts}

    def incr_and_get(self, key: str) -> int:
        self.counts[key] += 1
        return self.counts[key]


class MemcacheStore(Store):
    """
    TODO
    """

    def __init__(self, connection_string: str) -> None:
        self.log = logging.getLogger(self.__class__.__name__)
        self.client = pylibmc.Client([connection_string], binary=True)

    def get_multi(self, keys: List[str]) -> Dict[str, int]:
        raise NotImplemented()

    def incr_and_get(self, key: str, expire_s: int = 0) -> int:
        raise NotImplemented()
