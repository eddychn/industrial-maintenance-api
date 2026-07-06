"""
test_machines.py
----------------
Endpoint tests for machine management. These demonstrate API testing skills:
asserting on status codes, response bodies and validation behaviour.
"""

from __future__ import annotations


def test_create_machine_returns_201(client, sample_machine_payload):
    """Creating a machine returns 201 and echoes back the data with an id."""
    response = client.post("/api/machines", json=sample_machine_payload)
    assert response.status_code == 201

    body = response.json()
    assert body["id"] > 0
    assert body["name"] == sample_machine_payload["name"]
    assert body["status"] == "Running"


def test_get_machine_by_id(client, sample_machine_payload):
    """A created machine can be fetched back by its id."""
    created = client.post("/api/machines", json=sample_machine_payload).json()

    response = client.get(f"/api/machines/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_machine_returns_404(client):
    """Fetching an unknown machine returns 404 with a helpful message."""
    response = client.get("/api/machines/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_machines(client, sample_machine_payload):
    """The list endpoint returns all created machines."""
    client.post("/api/machines", json=sample_machine_payload)
    client.post("/api/machines", json=sample_machine_payload)

    response = client.get("/api/machines")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_machine(client, sample_machine_payload):
    """A partial update changes only the supplied fields."""
    created = client.post("/api/machines", json=sample_machine_payload).json()

    response = client.put(
        f"/api/machines/{created['id']}",
        json={"status": "Idle", "health_score": 55},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "Idle"
    assert body["health_score"] == 55
    assert body["name"] == sample_machine_payload["name"]  # unchanged


def test_delete_machine(client, sample_machine_payload):
    """Deleting a machine removes it; a subsequent GET returns 404."""
    created = client.post("/api/machines", json=sample_machine_payload).json()

    delete_response = client.delete(f"/api/machines/{created['id']}")
    assert delete_response.status_code == 200

    assert client.get(f"/api/machines/{created['id']}").status_code == 404


def test_invalid_health_score_rejected(client, sample_machine_payload):
    """Pydantic validation rejects an out-of-range health score with 422."""
    bad = {**sample_machine_payload, "health_score": 150}
    response = client.post("/api/machines", json=bad)
    assert response.status_code == 422


def test_invalid_status_rejected(client, sample_machine_payload):
    """An unknown enum value for status is rejected with 422."""
    bad = {**sample_machine_payload, "status": "Exploded"}
    response = client.post("/api/machines", json=bad)
    assert response.status_code == 422
