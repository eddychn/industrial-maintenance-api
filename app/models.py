"""
models.py
---------
SQLAlchemy ORM models -- the Python classes that map directly onto database
tables.

A "model" here is the *persistence* layer representation of our domain objects.
It is deliberately kept separate from the Pydantic *schemas* (see schemas.py)
which describe what the API sends and receives. Keeping these two layers apart
is a common industry pattern: the database shape and the API shape are allowed
to evolve independently.
"""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
# Using enums (instead of free-form strings) means the database, the ORM and the
# API all agree on the small, fixed set of valid values. Invalid values are
# rejected before they ever reach the database.
class MachineStatus(str, enum.Enum):
    """Operational state of a machine on the factory floor."""

    RUNNING = "Running"
    IDLE = "Idle"
    MAINTENANCE = "Maintenance"


class MaintenancePriority(str, enum.Enum):
    """How urgently a maintenance ticket needs attention."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class MaintenanceStatus(str, enum.Enum):
    """Lifecycle state of a maintenance ticket."""

    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CLOSED = "Closed"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
class Machine(Base):
    """A single physical asset (machine) on the factory floor.

    The ``health_score`` (0-100) is the primary signal used by the health
    monitoring and analytics endpoints to classify a machine as Healthy,
    Warning or Critical.
    """

    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    department = Column(String(120), nullable=False)
    manufacturer = Column(String(120), nullable=False)
    installation_date = Column(Date, nullable=False)
    operating_hours = Column(Float, nullable=False, default=0.0)
    health_score = Column(Float, nullable=False, default=100.0)
    status = Column(
        SqlEnum(MachineStatus),
        nullable=False,
        default=MachineStatus.IDLE,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # One machine can have many maintenance tickets over its lifetime.
    # ``cascade="all, delete-orphan"`` means deleting a machine also removes its
    # tickets, so we never leave orphaned rows behind.
    tickets = relationship(
        "MaintenanceTicket",
        back_populates="machine",
        cascade="all, delete-orphan",
    )


class MaintenanceTicket(Base):
    """A maintenance request raised against a specific machine."""

    __tablename__ = "maintenance_tickets"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(
        Integer,
        ForeignKey("machines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engineer_name = Column(String(120), nullable=True)
    priority = Column(
        SqlEnum(MaintenancePriority),
        nullable=False,
        default=MaintenancePriority.MEDIUM,
    )
    description = Column(Text, nullable=False)
    scheduled_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    status = Column(
        SqlEnum(MaintenanceStatus),
        nullable=False,
        default=MaintenanceStatus.OPEN,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # The reverse side of the Machine.tickets relationship.
    machine = relationship("Machine", back_populates="tickets")
