"""
schemas.py
----------
Pydantic models -- the "shape" of the data that flows in and out of the API.

Why a separate layer from ``models.py``?
    * SQLAlchemy models describe how data is *stored*.
    * Pydantic schemas describe how data is *validated and serialised* over HTTP.

FastAPI uses these classes to:
    1. Validate incoming request bodies (reject bad data with a 422 automatically).
    2. Convert database objects into clean JSON responses.
    3. Generate the interactive Swagger / OpenAPI documentation.

Naming convention used throughout:
    * ``XxxBase``   -> fields common to create and read.
    * ``XxxCreate`` -> what the client must send to create a resource.
    * ``XxxUpdate`` -> partial update (every field optional).
    * ``XxxRead``   -> what the API returns (includes server-generated fields).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .models import MachineStatus, MaintenancePriority, MaintenanceStatus


# ===========================================================================
# Machine schemas
# ===========================================================================
class MachineBase(BaseModel):
    """Fields a user supplies when describing a machine."""

    name: str = Field(..., min_length=1, max_length=120, examples=["CNC Lathe #4"])
    department: str = Field(..., min_length=1, max_length=120, examples=["Machining"])
    manufacturer: str = Field(..., min_length=1, max_length=120, examples=["Siemens"])
    installation_date: date = Field(..., examples=["2022-05-14"])
    operating_hours: float = Field(
        0.0, ge=0, description="Cumulative hours the machine has run."
    )
    health_score: float = Field(
        100.0,
        ge=0,
        le=100,
        description="Overall condition of the machine from 0 (failed) to 100 (perfect).",
    )
    status: MachineStatus = Field(
        default=MachineStatus.IDLE, description="Current operational status."
    )


class MachineCreate(MachineBase):
    """Payload for ``POST /api/machines``. Same fields as the base."""


class MachineUpdate(BaseModel):
    """Payload for ``PUT /api/machines/{id}``.

    Every field is optional so callers can send only the fields they want to
    change (a partial update). Validation constraints still apply to any field
    that *is* provided.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=120)
    department: Optional[str] = Field(None, min_length=1, max_length=120)
    manufacturer: Optional[str] = Field(None, min_length=1, max_length=120)
    installation_date: Optional[date] = None
    operating_hours: Optional[float] = Field(None, ge=0)
    health_score: Optional[float] = Field(None, ge=0, le=100)
    status: Optional[MachineStatus] = None


class MachineRead(MachineBase):
    """Machine as returned by the API, including server-managed fields."""

    id: int
    created_at: datetime
    updated_at: datetime

    # ``from_attributes=True`` lets Pydantic read data straight off SQLAlchemy
    # ORM objects (attribute access) instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# Maintenance ticket schemas
# ===========================================================================
class MaintenanceBase(BaseModel):
    """Common maintenance-ticket fields."""

    description: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        examples=["Spindle bearing making abnormal noise."],
    )
    priority: MaintenancePriority = Field(default=MaintenancePriority.MEDIUM)
    scheduled_date: Optional[date] = Field(
        None, description="When the maintenance is planned to take place."
    )
    engineer_name: Optional[str] = Field(
        None, max_length=120, description="Engineer assigned to the ticket."
    )


class MaintenanceCreate(MaintenanceBase):
    """Payload for ``POST /api/maintenance``.

    ``machine_id`` must reference an existing machine; the CRUD layer validates
    that and returns 404 if the machine does not exist.
    """

    machine_id: int = Field(..., gt=0, examples=[1])


class MaintenanceUpdate(BaseModel):
    """Partial update for a maintenance ticket."""

    engineer_name: Optional[str] = Field(None, max_length=120)
    priority: Optional[MaintenancePriority] = None
    description: Optional[str] = Field(None, min_length=3, max_length=1000)
    scheduled_date: Optional[date] = None
    completion_date: Optional[date] = None
    status: Optional[MaintenanceStatus] = None


class EngineerAssign(BaseModel):
    """Dedicated payload for the 'assign engineer' action."""

    engineer_name: str = Field(..., min_length=1, max_length=120, examples=["Priya Nair"])


class MaintenanceStatusUpdate(BaseModel):
    """Dedicated payload for changing only a ticket's status."""

    status: MaintenanceStatus


class MaintenanceRead(MaintenanceBase):
    """Maintenance ticket as returned by the API."""

    id: int
    machine_id: int
    completion_date: Optional[date] = None
    status: MaintenanceStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# Health monitoring schemas
# ===========================================================================
class HealthReport(BaseModel):
    """Human-readable health classification for a single machine."""

    machine_id: int
    machine_name: str
    health_score: float
    condition: str = Field(
        ..., description="One of: Healthy, Warning, Critical.", examples=["Healthy"]
    )


# ===========================================================================
# Analytics / dashboard schemas
# ===========================================================================
class DashboardSummary(BaseModel):
    """Aggregated KPIs shown on the maintenance dashboard."""

    total_machines: int
    machines_running: int
    machines_under_maintenance: int
    average_health_score: float
    critical_machines: int
    todays_maintenance_count: int


# ===========================================================================
# Predictive maintenance (AI/ML) schemas
# ===========================================================================
class MachinePrediction(BaseModel):
    """ML-predicted maintenance outlook for a single machine."""

    machine_id: int
    machine_name: str
    health_score: float
    operating_hours: float
    machine_age_days: int
    failure_risk: float = Field(
        ..., description="Predicted probability of needing maintenance soon (0-100%)."
    )
    risk_level: str = Field(..., description="Low, Medium, or High.")
    recommendation: str = Field(..., description="Suggested action for the engineer.")


# ===========================================================================
# Generic message schema
# ===========================================================================
class Message(BaseModel):
    """Simple ``{"detail": "..."}`` style response for delete/close actions."""

    detail: str
