import os
from typing import Dict
from typing import Type

from .rate_limiter.store import MemcacheStore
from .rate_limiter.store import MemoryStore
from .rate_limiter.store import Store


def store_backend() -> Store:
    store_backend: str = os.environ.get("STORE_BACKEND", "memory")
    if store_backend == "memcache":
        return MemcacheStore(memcache_connection_string())
    else:
        return MemoryStore()


def memcache_connection_string() -> str:
    """
    Return the connection string to connect to memcache.

    This reads the `MEMCACHE_CONNECTION_STRING` environment variable, and
    throws an exception if it is not present.

    :returns: the memcache connection string
    """
    return os.environ["MEMCACHE_CONNECTION_STRING"]
