from collections import defaultdict
from typing import Dict
from typing import List


class Store:
    """
    A counter store, that can be incremented and queried.

    TODO: have a memcache implementation
    """

    def __init__(self):
        self.counts: Dict[str, int] = defaultdict(int)

    def get_multi(self, keys: List[str]) -> Dict[str, int]:
        return {key: self.counts[key] for key in keys if key in self.counts}

    def incr_and_get(self, key: str) -> int:
        self.counts[key] += 1
        return self.counts[key]
