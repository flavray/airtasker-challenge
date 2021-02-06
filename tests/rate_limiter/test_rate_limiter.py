import time
from typing import Dict

import mock
import pytest

from airtasker_challenge.rate_limiter.rate_limiter import RateLimiter
from airtasker_challenge.rate_limiter.store import Store


class TestRateLimiter:

    @pytest.fixture
    def limiter(self) -> RateLimiter:
        return RateLimiter(permits=100, period_s=60 * 60, store=Store())

    def test_single_requestor(self, limiter: RateLimiter) -> None:
        for _ in range(100):
            assert limiter.try_acquire("requestor") == 0

        assert limiter.try_acquire("requestor") > 0

    def test_multiple_requestors(self, limiter: RateLimiter) -> None:
        for _ in range(100):
            assert limiter.try_acquire("requestor-1") == 0
            assert limiter.try_acquire("requestor-2") == 0

        assert limiter.try_acquire("requestor-1") > 0
        assert limiter.try_acquire("requestor-2") > 0
        assert limiter.try_acquire("requestor-3") == 0

    def test_permits(self) -> None:
        permits: int = 10

        limiter: RateLimiter = RateLimiter(
            permits=permits,
            period_s=60 * 60,
            store=Store(),
        )

        for _ in range(permits):
            assert limiter.try_acquire("requestor") == 0

        assert limiter.try_acquire("requestor") > 0

    def test_permits_refused_multiple_times(
        self, limiter: RateLimiter,
    ) -> None:
        for _ in range(100):
            limiter.try_acquire("requestor")

        # Ensure that permits are refused more than once
        for _ in range(42):
            assert limiter.try_acquire("requestor") > 0

    @mock.patch("time.time")
    def test_permits_time_passed(
        self, mock_time: mock.Mock, limiter: RateLimiter,
    ) -> None:
        # mock_time returns seconds since epoch

        # initial clock: beginning of times
        mock_time.return_value = 0

        for _ in range(100):
            limiter.try_acquire("requestor")

        assert limiter.try_acquire("requestor") > 0

        # clock: 40 * 60 seconds since epoch (rate limit still applies)
        mock_time.return_value = 40 * 60

        assert limiter.try_acquire("requestor") > 0

        # clock: 61 * 60 seconds since epoch (previous limit expired)
        mock_time.return_value = 61 * 60

        assert limiter.try_acquire("requestor") == 0

    def test_negative_permits(self) -> None:
        limiter: RateLimiter = RateLimiter(
            permits=-1, period_s=60 * 60, store=Store(),
        )

        for _ in range(1000):
            assert limiter.try_acquire("requestor") == 0

    def test_current_permits(self, limiter: RateLimiter) -> None:
        now_s: int = 0

        with mock.patch.object(
            limiter.store,
            "incr_and_get",
            return_value=42,
        ) as mock_incr_and_get:
            assert limiter._current_permits("requestor", now_s) == 42
            assert mock_incr_and_get.call_count == 1

    @pytest.mark.parametrize(
        "get_multi,expected",
        [
            # Each timestamp has a key associated with it.
            (
                {
                    "requestor-37": 10,
                    "requestor-38": 1,
                    "requestor-39": 5,
                    "requestor-40": 1,
                    "requestor-41": 1,
                },
                {
                    37: 10,
                    38: 1,
                    39: 5,
                    40: 1,
                    41: 1,
                },
            ),
            # Some timestamps have no key associated with them.
            (
                {
                    "requestor-37": 10,
                    "requestor-40": 1,
                    "requestor-41": 1,
                },
                {
                    37: 10,
                    40: 1,
                    41: 1,
                },
            ),
        ],
    )
    def test_previous_permits(
        self,
        get_multi: Dict[str, int],
        expected: Dict[int, int],
        limiter: RateLimiter,
    ) -> None:
        now_s: int = 42

        with mock.patch.object(
            limiter.store,
            "get_multi",
            return_value=get_multi,
            autospec=True,
        ):
            assert limiter._previous_permits("requestor", now_s) == expected

    def test_previous_store_keys(self) -> None:
        period_s: int = 5

        limiter: RateLimiter = RateLimiter(
            permits=1, period_s=period_s, store=Store(),
        )

        now_s: int = 42

        previous_keys: Dict[int, int] = limiter._previous_store_keys(
            "requestor", now_s,
        )

        expected_previous_keys = {
            37: "requestor-37",
            38: "requestor-38",
            39: "requestor-39",
            40: "requestor-40",
            41: "requestor-41",
        }

        assert previous_keys == expected_previous_keys

    def test_store_key(self, limiter: RateLimiter) -> None:
        assert limiter._store_key("requestor", 42) == "requestor-42"
