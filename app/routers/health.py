"""
routers/health.py
------------------
Health monitoring and analytics endpoints.

This router covers two of the assignment features:
    * Health Monitoring API  -> classify machines as Healthy / Warning / Critical.
    * Analytics Endpoints     -> the aggregated /api/dashboard summary.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..services.health_service import classify_health

router = APIRouter(prefix="/api", tags=["Health & Analytics"])


@router.get(
    "/health/machines",
    response_model=List[schemas.HealthReport],
    summary="Health classification for every machine",
)
def machines_health(db: Session = Depends(get_db)) -> List[schemas.HealthReport]:
    """Return a Healthy / Warning / Critical label for each machine.

    The numeric ``health_score`` is turned into a human-readable condition by the
    ``health_service`` so the classification rule lives in exactly one place.
    """
    machines = crud.get_machines(db, skip=0, limit=500)
    return [
        schemas.HealthReport(
            machine_id=m.id,
            machine_name=m.name,
            health_score=m.health_score,
            condition=classify_health(m.health_score),
        )
        for m in machines
    ]


@router.get(
    "/health/machines/{machine_id}",
    response_model=schemas.HealthReport,
    summary="Health classification for a single machine",
)
def machine_health(
    machine_id: int,
    db: Session = Depends(get_db),
) -> schemas.HealthReport:
    """Return the health condition of one machine, or **404** if unknown."""
    machine = crud.get_machine(db, machine_id)
    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine {machine_id} not found.",
        )
    return schemas.HealthReport(
        machine_id=machine.id,
        machine_name=machine.name,
        health_score=machine.health_score,
        condition=classify_health(machine.health_score),
    )


@router.get(
    "/dashboard",
    response_model=schemas.DashboardSummary,
    summary="Aggregated maintenance dashboard KPIs",
)
def dashboard(db: Session = Depends(get_db)) -> schemas.DashboardSummary:
    """Return the fleet-wide KPIs used by the maintenance dashboard.

    Includes total machines, how many are running / under maintenance, the
    average health score, how many are in a critical condition and how many
    maintenance jobs are scheduled for today.
    """
    return crud.get_dashboard_summary(db)
