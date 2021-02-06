import mock
import pytest
from typing import Dict
from typing import List

import pylibmc  # type: ignore

from airtasker_challenge.rate_limiter.store import MemcacheStore


class TestMemcacheStore:
    @pytest.fixture
    def store(self) -> MemcacheStore:
        with mock.patch("pylibmc.Client"):
            return MemcacheStore("memcached:11211")

    @pytest.mark.parametrize(
        "keys,in_memcache,expected",
        [
            # All keys have a value associated with them
            (
                ["key-1", "key-2", "key-3"],
                {"key-1": 1, "key-2": 4, "key-3": 3},
                {"key-1": 1, "key-2": 4, "key-3": 3},
            ),
            # Some keys do not have a value associated with them
            (
                ["key-1", "key-2", "key-3"],
                {"key-1": 1},
                {"key-1": 1},
            ),
        ],
    )
    def test_get_multi(
        self,
        keys: List[str],
        in_memcache: Dict[str, int],
        expected: Dict[str, int],
        store: MemcacheStore,
    ) -> None:
        with mock.patch.object(
            store.client,
            "get_multi",
            return_value=in_memcache,
            autospec=True,
        ) as mock_get_multi:
            assert store.get_multi(keys) == expected
            assert mock_get_multi.call_count == 1

    def test_get_multi_exception(self, store: MemcacheStore) -> None:
        with mock.patch.object(
            store.client,
            "get_multi",
            side_effect=pylibmc.Error("an error occurred"),
            autospec=True,
        ) as mock_get_multi:
            assert store.get_multi(["key-1", "key-2"]) == {}
            assert mock_get_multi.call_count == 1

    def test_incr_and_get(self, store: MemcacheStore) -> None:
        count: int = 42

        with mock.patch.object(
            store.client,
            "incr",
            return_value=count,
            autospec=True,
        ) as mock_incr_and_get:
            assert store.incr_and_get("key") == count
            assert mock_incr_and_get.call_count == 1

    def test_incr_and_get_exception(self, store: MemcacheStore) -> None:
        # Ensure incr_and_get returns 0 upon a memcache exception
        with mock.patch.object(
            store.client,
            "incr",
            side_effect=pylibmc.Error("an error occurred"),
            autospec=True,
        ) as mock_incr_and_get:
            assert store.incr_and_get("key") == 0
            assert mock_incr_and_get.call_count == 1

    def test_decr_exception(self, store: MemcacheStore) -> None:
        with mock.patch.object(
            store.client,
            "decr",
            side_effect=pylibmc.Error("an error occurred"),
            autospec=True,
        ) as mock_decr:
            store.decr("key")
            assert mock_decr.call_count == 1
