from flask import Flask

from .rate_limiter import rate_limited
from .rate_limiter.store import Store


app: Flask = Flask(__name__)


@app.route("/")
@rate_limited(permits=100, period_s=60 * 60, store=Store())
def hello() -> str:
    return "Hello, world!"
