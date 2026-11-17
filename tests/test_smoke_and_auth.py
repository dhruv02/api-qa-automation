"""Smoke, security boundary and HTTP status assertions."""

import requests
import pytest


@pytest.mark.smoke
def test_health_is_available(base_url):
    response = requests.get(f"{base_url}/health", timeout=5)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.auth
@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_invalid_auth_returns_401(base_url, headers):
    response = requests.get(f"{base_url}/tickets", headers=headers, timeout=5)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


@pytest.mark.auth
def test_write_requires_auth(base_url):
    response = requests.post(f"{base_url}/tickets", json={"title": "A test"}, timeout=5)
    assert response.status_code == 401


@pytest.mark.smoke
def test_empty_list_is_valid(api, base_url):
    response = api.get(f"{base_url}/tickets", timeout=5)
    assert response.status_code == 200
    assert response.json() == {"items": [], "count": 0}
