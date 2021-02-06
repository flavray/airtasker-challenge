import pytest
from flask.testing import FlaskClient

from airtasker_challenge.app import app


class TestApp:

    @pytest.fixture
    def client(self) -> FlaskClient:
        return app.test_client()

    def test_hello(self, client: FlaskClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
