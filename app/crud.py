"""
crud.py
-------
The data-access layer. CRUD stands for Create, Read, Update, Delete -- the four
basic operations any persistent store supports.

Every function here takes a database ``Session`` plus plain arguments and returns
ORM objects. Keeping *all* database queries in this single module (instead of
scattering them across the routers) gives us a clean separation of concerns:

    routers  -> handle HTTP (status codes, request/response)
    crud     -> handle the database
    models   -> define the tables
    schemas  -> define the API contract

This is the "thin controller, fat service" pattern used in most production
FastAPI code bases.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas


# ===========================================================================
# Machine CRUD
# ===========================================================================
def get_machine(db: Session, machine_id: int) -> Optional[models.Machine]:
    """Return a single machine by primary key, or ``None`` if not found."""
    return db.query(models.Machine).filter(models.Machine.id == machine_id).first()


def get_machines(db: Session, skip: int = 0, limit: int = 100) -> List[models.Machine]:
    """Return a paginated list of machines, newest first."""
    return (
        db.query(models.Machine)
        .order_by(models.Machine.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_machine(db: Session, machine: schemas.MachineCreate) -> models.Machine:
    """Insert a new machine and return the persisted row (with its new ID)."""
    db_machine = models.Machine(**machine.model_dump())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)  # reload so server-generated fields (id, timestamps) are populated
    return db_machine


def update_machine(
    db: Session, db_machine: models.Machine, updates: schemas.MachineUpdate
) -> models.Machine:
    """Apply a partial update to an existing machine.

    ``exclude_unset=True`` ensures we only touch the fields the caller actually
    sent, leaving everything else untouched.
    """
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_machine, field, value)
    db.commit()
    db.refresh(db_machine)
    return db_machine


def delete_machine(db: Session, db_machine: models.Machine) -> None:
    """Delete a machine (and, via cascade, all of its maintenance tickets)."""
    db.delete(db_machine)
    db.commit()


# ===========================================================================
# Maintenance CRUD
# ===========================================================================
def get_ticket(db: Session, ticket_id: int) -> Optional[models.MaintenanceTicket]:
    """Return a single maintenance ticket by primary key."""
    return (
        db.query(models.MaintenanceTicket)
        .filter(models.MaintenanceTicket.id == ticket_id)
        .first()
    )


def get_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    machine_id: Optional[int] = None,
    status: Optional[models.MaintenanceStatus] = None,
) -> List[models.MaintenanceTicket]:
    """Return maintenance tickets, optionally filtered by machine or status."""
    query = db.query(models.MaintenanceTicket)
    if machine_id is not None:
        query = query.filter(models.MaintenanceTicket.machine_id == machine_id)
    if status is not None:
        query = query.filter(models.MaintenanceTicket.status == status)
    return (
        query.order_by(models.MaintenanceTicket.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_ticket(
    db: Session, ticket: schemas.MaintenanceCreate
) -> models.MaintenanceTicket:
    """Insert a new maintenance ticket.

    The caller (router) is responsible for having already verified that the
    referenced machine exists.
    """
    db_ticket = models.MaintenanceTicket(**ticket.model_dump())
    db.add(db_ticket)

    # Business rule: raising a ticket puts the machine into MAINTENANCE status so
    # the shop floor immediately reflects that the asset needs attention.
    machine = get_machine(db, ticket.machine_id)
    if machine is not None:
        machine.status = models.MachineStatus.MAINTENANCE

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket(
    db: Session,
    db_ticket: models.MaintenanceTicket,
    updates: schemas.MaintenanceUpdate,
) -> models.MaintenanceTicket:
    """Apply a partial update to a maintenance ticket."""
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_ticket, field, value)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def assign_engineer(
    db: Session, db_ticket: models.MaintenanceTicket, engineer_name: str
) -> models.MaintenanceTicket:
    """Assign an engineer and move an OPEN ticket to IN_PROGRESS."""
    db_ticket.engineer_name = engineer_name
    if db_ticket.status == models.MaintenanceStatus.OPEN:
        db_ticket.status = models.MaintenanceStatus.IN_PROGRESS
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def set_ticket_status(
    db: Session,
    db_ticket: models.MaintenanceTicket,
    status: models.MaintenanceStatus,
) -> models.MaintenanceTicket:
    """Change a ticket's status, stamping the completion date when relevant."""
    db_ticket.status = status
    if status in (
        models.MaintenanceStatus.COMPLETED,
        models.MaintenanceStatus.CLOSED,
    ):
        db_ticket.completion_date = db_ticket.completion_date or date.today()
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def close_ticket(
    db: Session, db_ticket: models.MaintenanceTicket
) -> models.MaintenanceTicket:
    """Close a maintenance ticket and return the machine to RUNNING.

    Closing the last open ticket for a machine signals that the asset has been
    serviced, so we flip it back from MAINTENANCE to RUNNING.
    """
    db_ticket.status = models.MaintenanceStatus.CLOSED
    db_ticket.completion_date = db_ticket.completion_date or date.today()

    machine = get_machine(db, db_ticket.machine_id)
    if machine is not None:
        open_tickets = (
            db.query(models.MaintenanceTicket)
            .filter(
                models.MaintenanceTicket.machine_id == machine.id,
                models.MaintenanceTicket.status.in_(
                    [
                        models.MaintenanceStatus.OPEN,
                        models.MaintenanceStatus.IN_PROGRESS,
                    ]
                ),
                models.MaintenanceTicket.id != db_ticket.id,
            )
            .count()
        )
        if open_tickets == 0:
            machine.status = models.MachineStatus.RUNNING

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


# ===========================================================================
# Analytics helpers
# ===========================================================================
def get_dashboard_summary(db: Session) -> schemas.DashboardSummary:
    """Compute the aggregated KPIs for the dashboard endpoint.

    All aggregation is pushed down into SQL (``func.count`` / ``func.avg``) so
    the database does the heavy lifting rather than pulling every row into
    Python.
    """
    total_machines = db.query(func.count(models.Machine.id)).scalar() or 0

    machines_running = (
        db.query(func.count(models.Machine.id))
        .filter(models.Machine.status == models.MachineStatus.RUNNING)
        .scalar()
        or 0
    )

    machines_under_maintenance = (
        db.query(func.count(models.Machine.id))
        .filter(models.Machine.status == models.MachineStatus.MAINTENANCE)
        .scalar()
        or 0
    )

    average_health = db.query(func.avg(models.Machine.health_score)).scalar()
    average_health_score = round(float(average_health), 2) if average_health else 0.0

    # "Critical" mirrors the health-monitoring rule: score below 40.
    critical_machines = (
        db.query(func.count(models.Machine.id))
        .filter(models.Machine.health_score < 40)
        .scalar()
        or 0
    )

    todays_maintenance_count = (
        db.query(func.count(models.MaintenanceTicket.id))
        .filter(models.MaintenanceTicket.scheduled_date == date.today())
        .scalar()
        or 0
    )

    return schemas.DashboardSummary(
        total_machines=total_machines,
        machines_running=machines_running,
        machines_under_maintenance=machines_under_maintenance,
        average_health_score=average_health_score,
        critical_machines=critical_machines,
        todays_maintenance_count=todays_maintenance_count,
    )
