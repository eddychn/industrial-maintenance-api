"""
test_predictions.py
-------------------
Tests for the predictive-maintenance (AI/ML) endpoints.

We avoid asserting exact risk numbers (an ML model's output is probabilistic).
Instead we assert on structure, valid ranges, and the *relationship* the model
should have learned: a worn-out machine must be riskier than a brand-new one.
"""

from __future__ import annotations


def _make_machine(client, name, health, hours, installed):
    payload = {
        "name": name,
        "department": "Machining",
        "manufacturer": "Siemens",
        "installation_date": installed,
        "operating_hours": hours,
        "health_score": health,
        "status": "Running",
    }
    return client.post("/api/machines", json=payload).json()


def test_prediction_structure_and_ranges(client):
    """A prediction returns all fields with valid ranges."""
    machine = _make_machine(client, "Press A", 60, 20000, "2021-01-01")

    response = client.get(f"/api/predictions/machines/{machine['id']}")
    assert response.status_code == 200

    body = response.json()
    assert 0 <= body["failure_risk"] <= 100
    assert body["risk_level"] in {"Low", "Medium", "High"}
    assert len(body["recommendation"]) > 0
    assert body["machine_age_days"] >= 0


def test_worn_machine_is_riskier_than_new_machine(client):
    """The model must rank a worn, old, unhealthy machine above a fresh one."""
    good = _make_machine(client, "Fresh Machine", 95, 500, "2025-06-01")
    bad = _make_machine(client, "Worn Machine", 10, 58000, "2016-01-01")

    good_risk = client.get(f"/api/predictions/machines/{good['id']}").json()["failure_risk"]
    bad_risk = client.get(f"/api/predictions/machines/{bad['id']}").json()["failure_risk"]

    assert bad_risk > good_risk


def test_prediction_for_missing_machine_returns_404(client):
    response = client.get("/api/predictions/machines/999")
    assert response.status_code == 404


def test_at_risk_endpoint_returns_only_high_risk(client):
    """The at-risk endpoint returns only High-risk machines."""
    _make_machine(client, "Healthy", 98, 200, "2025-06-01")
    _make_machine(client, "Failing", 5, 59000, "2015-01-01")

    response = client.get("/api/predictions/at-risk")
    assert response.status_code == 200
    for item in response.json():
        assert item["risk_level"] == "High"
