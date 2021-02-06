from flask import Flask

from .rate_limiter import rate_limited


app: Flask = Flask(__name__)


@app.route("/")
@rate_limited(permits=100, period_s=60 * 60)
def hello() -> str:
    return "Hello, world!"
