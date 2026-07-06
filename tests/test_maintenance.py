"""
test_maintenance.py
-------------------
Endpoint tests for the maintenance module and the machine-status side effects
it triggers.
"""

from __future__ import annotations

import pytest


@pytest.fixture()
def machine_id(client, sample_machine_payload) -> int:
    """Create a machine and return its id for use in maintenance tests."""
    return client.post("/api/machines", json=sample_machine_payload).json()["id"]


def test_create_ticket_sets_machine_to_maintenance(client, machine_id):
    """Raising a ticket returns 201 and flips the machine to Maintenance."""
    response = client.post(
        "/api/maintenance",
        json={
            "machine_id": machine_id,
            "description": "Spindle bearing noise.",
            "priority": "High",
            "scheduled_date": "2026-07-02",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "Open"

    machine = client.get(f"/api/machines/{machine_id}").json()
    assert machine["status"] == "Maintenance"


def test_create_ticket_for_missing_machine_returns_404(client):
    """A ticket against a non-existent machine is rejected with 404."""
    response = client.post(
        "/api/maintenance",
        json={"machine_id": 999, "description": "does not matter"},
    )
    assert response.status_code == 404


def test_assign_engineer_moves_to_in_progress(client, machine_id):
    """Assigning an engineer to an Open ticket moves it to In Progress."""
    ticket = client.post(
        "/api/maintenance",
        json={"machine_id": machine_id, "description": "Check hydraulics."},
    ).json()

    response = client.patch(
        f"/api/maintenance/{ticket['id']}/assign",
        json={"engineer_name": "Priya Nair"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["engineer_name"] == "Priya Nair"
    assert body["status"] == "In Progress"


def test_update_status_sets_completion_date(client, machine_id):
    """Marking a ticket Completed auto-stamps a completion date."""
    ticket = client.post(
        "/api/maintenance",
        json={"machine_id": machine_id, "description": "Replace filter."},
    ).json()

    response = client.patch(
        f"/api/maintenance/{ticket['id']}/status",
        json={"status": "Completed"},
    )
    assert response.status_code == 200
    assert response.json()["completion_date"] is not None


def test_close_ticket_returns_machine_to_running(client, machine_id):
    """Closing the machine's only open ticket returns it to Running."""
    ticket = client.post(
        "/api/maintenance",
        json={"machine_id": machine_id, "description": "Lubricate rails."},
    ).json()

    response = client.post(f"/api/maintenance/{ticket['id']}/close")
    assert response.status_code == 200
    assert response.json()["status"] == "Closed"

    machine = client.get(f"/api/machines/{machine_id}").json()
    assert machine["status"] == "Running"


def test_filter_tickets_by_machine(client, machine_id):
    """The list endpoint can be filtered by machine_id."""
    client.post(
        "/api/maintenance",
        json={"machine_id": machine_id, "description": "Job A."},
    )
    response = client.get(f"/api/maintenance?machine_id={machine_id}")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_short_description_rejected(client, machine_id):
    """Description shorter than 3 chars is rejected by validation (422)."""
    response = client.post(
        "/api/maintenance",
        json={"machine_id": machine_id, "description": "x"},
    )
    assert response.status_code == 422
