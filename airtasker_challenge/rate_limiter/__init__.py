from functools import wraps

from flask import request

from .rate_limiter import RateLimiter
from .store import Store


def rate_limited(permits: int, period_s: int, store: Store):
    """
    A Flask decorator to add IP address-based rate limiting for a route.

    If a requestor reached their limit of request permits over the given
    period, a HTTP 429 (Too Many Requests) response will be returned,
    indicating the time (in seconds) to wait until the next request can be
    made.

    :param permits: the number of calls that can be made over a period of time.
    :param period_s: the duration (in seconds) of a period
    """

    limiter = RateLimiter(permits=permits, period_s=period_s, store=store)

    def decorated_rate_limit(func):
        @wraps(func)
        def rate_limited_route(*args, **kwargs):
            requestor_ip: str = request.remote_addr
            cooldown_s: int = limiter.try_acquire(requestor_ip)

            if cooldown_s > 0:
                return (
                    f"Rate limit exceeded. Try again in #{cooldown_s} seconds",
                    429,
                )

            return func(*args, **kwargs)

        return rate_limited_route

    return decorated_rate_limit
