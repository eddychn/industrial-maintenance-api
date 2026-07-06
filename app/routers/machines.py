"""
routers/machines.py
--------------------
HTTP endpoints for machine management (the "Machine Management" feature).

Responsibilities of a router module:
    * Declare routes and their HTTP methods.
    * Validate the resource exists (returning 404 when it does not).
    * Return the correct HTTP status codes.
    * Delegate all database work to ``crud.py``.

It deliberately contains no raw SQL -- that lives in the CRUD layer.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

# ``prefix`` means every route below is automatically mounted under /api/machines.
# ``tags`` groups these endpoints together in the Swagger UI.
router = APIRouter(prefix="/api/machines", tags=["Machines"])


@router.post(
    "",
    response_model=schemas.MachineRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new machine",
)
def create_machine(
    machine: schemas.MachineCreate,
    db: Session = Depends(get_db),
) -> schemas.MachineRead:
    """Create a machine.

    Returns **201 Created** with the newly persisted machine (including its
    server-assigned ``id``).
    """
    return crud.create_machine(db, machine)


@router.get(
    "",
    response_model=List[schemas.MachineRead],
    summary="List all machines",
)
def list_machines(
    skip: int = Query(0, ge=0, description="Number of records to skip (pagination)."),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return."),
    db: Session = Depends(get_db),
) -> List[schemas.MachineRead]:
    """Return all machines, most recently created first."""
    return crud.get_machines(db, skip=skip, limit=limit)


@router.get(
    "/{machine_id}",
    response_model=schemas.MachineRead,
    summary="Get a single machine by ID",
)
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db),
) -> schemas.MachineRead:
    """Fetch one machine. Returns **404** if the ID does not exist."""
    machine = crud.get_machine(db, machine_id)
    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine {machine_id} not found.",
        )
    return machine


@router.put(
    "/{machine_id}",
    response_model=schemas.MachineRead,
    summary="Update an existing machine",
)
def update_machine(
    machine_id: int,
    updates: schemas.MachineUpdate,
    db: Session = Depends(get_db),
) -> schemas.MachineRead:
    """Partially update a machine. Returns **404** if it does not exist."""
    machine = crud.get_machine(db, machine_id)
    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine {machine_id} not found.",
        )
    return crud.update_machine(db, machine, updates)


@router.delete(
    "/{machine_id}",
    response_model=schemas.Message,
    summary="Delete a machine",
)
def delete_machine(
    machine_id: int,
    db: Session = Depends(get_db),
) -> schemas.Message:
    """Delete a machine and all of its maintenance tickets (via cascade)."""
    machine = crud.get_machine(db, machine_id)
    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine {machine_id} not found.",
        )
    crud.delete_machine(db, machine)
    return schemas.Message(detail=f"Machine {machine_id} deleted successfully.")
