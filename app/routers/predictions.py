"""
routers/predictions.py
----------------------
Predictive-maintenance (AI/ML) endpoints.

These expose the machine-learning model in ``app/ml/model.py`` over the API so
engineers can ask, for any machine, *"how likely is this to need maintenance
soon, and what should I do?"* -- the core predictive-maintenance use case.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db
from ..ml.model import predict_failure_risk

router = APIRouter(prefix="/api/predictions", tags=["Predictive Maintenance (AI/ML)"])


def _predict_for_machine(machine: models.Machine) -> schemas.MachinePrediction:
    """Run the ML model for one machine and build the response object."""
    result = predict_failure_risk(
        operating_hours=machine.operating_hours,
        health_score=machine.health_score,
        installation_date=machine.installation_date,
        status=machine.status.value if machine.status else None,
    )
    return schemas.MachinePrediction(
        machine_id=machine.id,
        machine_name=machine.name,
        health_score=machine.health_score,
        operating_hours=machine.operating_hours,
        machine_age_days=result["machine_age_days"],
        failure_risk=result["failure_risk"],
        risk_level=result["risk_level"],
        recommendation=result["recommendation"],
    )


@router.get(
    "/machines/{machine_id}",
    response_model=schemas.MachinePrediction,
    summary="Predict maintenance failure risk for one machine",
)
def predict_machine(
    machine_id: int,
    db: Session = Depends(get_db),
) -> schemas.MachinePrediction:
    """Return the ML-predicted failure risk and recommended action for a machine.

    Returns **404** if the machine does not exist.
    """
    machine = crud.get_machine(db, machine_id)
    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine {machine_id} not found.",
        )
    return _predict_for_machine(machine)


@router.get(
    "/machines",
    response_model=List[schemas.MachinePrediction],
    summary="Predict failure risk for every machine",
)
def predict_all_machines(db: Session = Depends(get_db)) -> List[schemas.MachinePrediction]:
    """Return predictions for all machines, most recently added first."""
    machines = crud.get_machines(db, skip=0, limit=500)
    return [_predict_for_machine(m) for m in machines]


@router.get(
    "/at-risk",
    response_model=List[schemas.MachinePrediction],
    summary="List machines predicted to be at high risk",
)
def machines_at_risk(db: Session = Depends(get_db)) -> List[schemas.MachinePrediction]:
    """Return only the machines the model flags as **High** risk.

    This is the endpoint a maintenance dashboard would poll to surface the
    machines that need attention *before* they break down.
    """
    machines = crud.get_machines(db, skip=0, limit=500)
    predictions = [_predict_for_machine(m) for m in machines]
    high = [p for p in predictions if p.risk_level == "High"]
    # Most urgent first.
    high.sort(key=lambda p: p.failure_risk, reverse=True)
    return high
