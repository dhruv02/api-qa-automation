"""API contract, lifecycle and negative test cases using HTTP requests."""

import pytest
from jsonschema import validate

TICKET_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "priority", "status"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "title": {"type": "string", "minLength": 3},
        "priority": {"enum": ["low", "medium", "high"]},
        "status": {"const": "open"},
    },
}


@pytest.mark.contract
@pytest.mark.parametrize("priority", ["low", "medium", "high"])
def test_create_ticket_contract(api, base_url, priority):
    response = api.post(
        f"{base_url}/tickets", json={"title": "  Delivery issue  ", "priority": priority}, timeout=5
    )
    assert response.status_code == 201
    body = response.json()
    validate(body, TICKET_SCHEMA)
    assert body["title"] == "Delivery issue"
    assert body["priority"] == priority


@pytest.mark.contract
def test_create_read_delete_lifecycle(api, base_url, create_ticket):
    ticket = create_ticket(title="Customer follow-up")
    response = api.get(f"{base_url}/tickets/{ticket['id']}", timeout=5)
    assert response.status_code == 200
    assert response.json() == ticket

    removed = api.delete(f"{base_url}/tickets/{ticket['id']}", timeout=5)
    assert removed.status_code == 204
    assert removed.text == ""
    assert api.get(f"{base_url}/tickets/{ticket['id']}", timeout=5).status_code == 404


@pytest.mark.contract
def test_list_and_priority_filter(api, base_url, create_ticket):
    create_ticket(title="Low priority question", priority="low")
    high = create_ticket(title="Payment outage", priority="high")
    response = api.get(f"{base_url}/tickets", params={"priority": "high"}, timeout=5)
    assert response.status_code == 200
    assert response.json() == {"items": [high], "count": 1}


@pytest.mark.contract
def test_list_limit(api, base_url, create_ticket):
    create_ticket(title="First ticket")
    create_ticket(title="Second ticket")
    response = api.get(f"{base_url}/tickets", params={"limit": 1}, timeout=5)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["count"] == 2


@pytest.mark.negative
@pytest.mark.parametrize(
    "payload",
    [
        {"title": "ok", "priority": "high"},
        {"title": "   ", "priority": "high"},
        {"title": "Missing order", "priority": "urgent"},
        {"title": "Missing order", "priority": 123},
    ],
)
def test_invalid_payloads_return_422(api, base_url, payload):
    response = api.post(f"{base_url}/tickets", json=payload, timeout=5)
    assert response.status_code == 422


@pytest.mark.negative
def test_unknown_ticket_returns_404(api, base_url):
    assert api.get(f"{base_url}/tickets/9999", timeout=5).status_code == 404
    assert api.delete(f"{base_url}/tickets/9999", timeout=5).status_code == 404


@pytest.mark.negative
def test_invalid_query_parameter_returns_422(api, base_url):
    assert api.get(f"{base_url}/tickets", params={"limit": 0}, timeout=5).status_code == 422
