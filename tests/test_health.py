"""
Smoke tests using a test-only FastAPI app.
No database, no lifespan, no external services required.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router as api_router


@pytest.fixture(scope="module")
def client():
    """
    Build a minimal FastAPI app using the same router as production
    but with no lifespan (no DB connection attempt).
    """
    test_app = FastAPI()
    test_app.include_router(api_router)
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_topics_endpoint_reachable(client: TestClient) -> None:
    response = client.get("/topics")
    assert response.status_code != 404


def test_articles_endpoint_reachable(client: TestClient) -> None:
    response = client.get("/articles")
    assert response.status_code != 404


def test_newsletters_endpoint_reachable(client: TestClient) -> None:
    response = client.get("/newsletters")
    assert response.status_code != 404


def test_subscribers_endpoint_reachable(client: TestClient) -> None:
    response = client.get("/subscribers")
    assert response.status_code != 404
