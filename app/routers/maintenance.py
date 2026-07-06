"""
routers/maintenance.py
-----------------------
HTTP endpoints for the maintenance module: raising tickets, assigning engineers,
updating status and closing tickets.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/maintenance", tags=["Maintenance"])


def _get_ticket_or_404(db: Session, ticket_id: int) -> models.MaintenanceTicket:
    """Small helper to fetch a ticket or raise a consistent 404.

    Factoring this out avoids repeating the same four lines in every handler.
    """
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance ticket {ticket_id} not found.",
        )
    return ticket


@router.post(
    "",
    response_model=schemas.MaintenanceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a maintenance request",
)
def create_ticket(
    ticket: schemas.MaintenanceCreate,
    db: Session = Depends(get_db),
) -> schemas.MaintenanceRead:
    """Raise a maintenance ticket against an existing machine.

    Returns **404** if the referenced ``machine_id`` does not exist, otherwise
    **201 Created** with the new ticket. Creating a ticket also flips the target
    machine into the ``Maintenance`` status.
    """
    if crud.get_machine(db, ticket.machine_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine {ticket.machine_id} not found; cannot raise ticket.",
        )
    return crud.create_ticket(db, ticket)


@router.get(
    "",
    response_model=List[schemas.MaintenanceRead],
    summary="List maintenance tickets",
)
def list_tickets(
    machine_id: Optional[int] = Query(None, description="Filter by machine ID."),
    ticket_status: Optional[models.MaintenanceStatus] = Query(
        None, description="Filter by ticket status."
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[schemas.MaintenanceRead]:
    """Return maintenance tickets, optionally filtered by machine and/or status."""
    return crud.get_tickets(
        db, skip=skip, limit=limit, machine_id=machine_id, status=ticket_status
    )


@router.get(
    "/{ticket_id}",
    response_model=schemas.MaintenanceRead,
    summary="Get a maintenance ticket by ID",
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> schemas.MaintenanceRead:
    """Fetch a single ticket, or **404** if it does not exist."""
    return _get_ticket_or_404(db, ticket_id)


@router.patch(
    "/{ticket_id}/assign",
    response_model=schemas.MaintenanceRead,
    summary="Assign an engineer to a ticket",
)
def assign_engineer(
    ticket_id: int,
    payload: schemas.EngineerAssign,
    db: Session = Depends(get_db),
) -> schemas.MaintenanceRead:
    """Assign an engineer. An ``Open`` ticket automatically becomes ``In Progress``."""
    ticket = _get_ticket_or_404(db, ticket_id)
    return crud.assign_engineer(db, ticket, payload.engineer_name)


@router.patch(
    "/{ticket_id}/status",
    response_model=schemas.MaintenanceRead,
    summary="Update the status of a ticket",
)
def update_status(
    ticket_id: int,
    payload: schemas.MaintenanceStatusUpdate,
    db: Session = Depends(get_db),
) -> schemas.MaintenanceRead:
    """Change a ticket's status. Completing/closing stamps the completion date."""
    ticket = _get_ticket_or_404(db, ticket_id)
    return crud.set_ticket_status(db, ticket, payload.status)


@router.put(
    "/{ticket_id}",
    response_model=schemas.MaintenanceRead,
    summary="Update a maintenance ticket",
)
def update_ticket(
    ticket_id: int,
    updates: schemas.MaintenanceUpdate,
    db: Session = Depends(get_db),
) -> schemas.MaintenanceRead:
    """Partially update any field of a maintenance ticket."""
    ticket = _get_ticket_or_404(db, ticket_id)
    return crud.update_ticket(db, ticket, updates)


@router.post(
    "/{ticket_id}/close",
    response_model=schemas.MaintenanceRead,
    summary="Close a maintenance ticket",
)
def close_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
) -> schemas.MaintenanceRead:
    """Close a ticket. If it was the machine's last open ticket, the machine is
    returned to ``Running`` status."""
    ticket = _get_ticket_or_404(db, ticket_id)
    return crud.close_ticket(db, ticket)
