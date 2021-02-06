import os

from flask import Flask

from .config import store_backend
from .rate_limiter import rate_limited
from .rate_limiter.store import MemcacheStore


app: Flask = Flask(__name__)


@app.route("/")
@rate_limited(permits=100, period_s=60 * 60, store=store_backend())
def hello() -> str:
    return "Hello, world!"
