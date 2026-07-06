"""
test_health_and_dashboard.py
----------------------------
Tests for the health-classification rules and the aggregated dashboard KPIs.
"""

from __future__ import annotations

import pytest

from app.services.health_service import classify_health


# ---------------------------------------------------------------------------
# Pure unit tests for the classification rule (no HTTP, no DB needed).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "score,expected",
    [
        (95, "Healthy"),
        (70, "Healthy"),   # boundary: >= 70
        (69.9, "Warning"),
        (40, "Warning"),   # boundary: >= 40
        (39.9, "Critical"),
        (0, "Critical"),
    ],
)
def test_classify_health(score, expected):
    assert classify_health(score) == expected


# ---------------------------------------------------------------------------
# Endpoint tests.
# ---------------------------------------------------------------------------
def _make_machine(client, name, health):
    payload = {
        "name": name,
        "department": "Machining",
        "manufacturer": "Siemens",
        "installation_date": "2022-05-14",
        "operating_hours": 100,
        "health_score": health,
        "status": "Running",
    }
    return client.post("/api/machines", json=payload).json()


def test_machine_health_endpoint(client):
    machine = _make_machine(client, "Press A", 30)
    response = client.get(f"/api/health/machines/{machine['id']}")
    assert response.status_code == 200
    assert response.json()["condition"] == "Critical"


def test_dashboard_summary(client):
    """The dashboard aggregates counts and averages correctly."""
    _make_machine(client, "Healthy Machine", 90)
    _make_machine(client, "Critical Machine", 20)

    response = client.get("/api/dashboard")
    assert response.status_code == 200

    body = response.json()
    assert body["total_machines"] == 2
    assert body["machines_running"] == 2
    assert body["critical_machines"] == 1
    assert body["average_health_score"] == 55.0
