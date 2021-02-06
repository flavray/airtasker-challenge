import pytest
from flask.testing import FlaskClient

from airtasker_challenge.app import app


class TestApp:
    @pytest.fixture
    def client(self) -> FlaskClient:
        return app.test_client()

    def test_rate_limited(self, client: FlaskClient) -> None:
        for _ in range(100):
            assert client.get("/").status_code == 200

        assert client.get("/").status_code == 429
