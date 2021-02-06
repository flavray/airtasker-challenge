from flask import Flask


app: Flask = Flask(__name__)


@app.route("/")
def hello() -> str:
    return "Hello, world!"
