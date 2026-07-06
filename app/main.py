"""
main.py
-------
Application entry point. This is the file Uvicorn loads (``app.main:app``).

Responsibilities:
    * Create the FastAPI application object and its metadata (title, version,
      description) which powers the automatically generated Swagger UI.
    * Create the database tables on first run.
    * Mount the routers (machines, maintenance, health & analytics).
    * Expose a couple of top-level convenience endpoints (root + liveness).
"""

from __future__ import annotations

from fastapi import FastAPI

from . import __version__
from .database import Base, engine
from .routers import health, machines, maintenance

# ---------------------------------------------------------------------------
# Create tables.
# ---------------------------------------------------------------------------
# ``create_all`` inspects every model that inherits from ``Base`` and issues the
# CREATE TABLE statements for any table that does not yet exist. This is what
# makes the SQLite database appear automatically on first run. (For a real
# production system you would replace this with Alembic migrations.)
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Application object.
# ---------------------------------------------------------------------------
# The description below is rendered at the top of the Swagger UI (/docs).
app = FastAPI(
    title="Industrial Asset Maintenance Management API",
    version=__version__,
    description=(
        "A production-style REST API for a manufacturing company to manage "
        "factory machines, schedule maintenance, report faults and monitor "
        "machine health.\n\n"
        "Interactive docs: **/docs** (Swagger UI) and **/redoc** (ReDoc)."
    ),
    contact={"name": "Maintenance Engineering Team"},
    license_info={"name": "MIT"},
)

# ---------------------------------------------------------------------------
# Mount routers.
# ---------------------------------------------------------------------------
app.include_router(machines.router)
app.include_router(maintenance.router)
app.include_router(health.router)


@app.get("/", tags=["Root"], summary="API root / welcome message")
def root() -> dict:
    """Simple landing endpoint pointing callers to the documentation."""
    return {
        "message": "Industrial Asset Maintenance Management API",
        "version": __version__,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Root"], summary="Service liveness probe")
def liveness() -> dict:
    """Lightweight liveness check for load balancers / container orchestrators.

    (Distinct from the *machine* health endpoints under ``/api/health``.)
    """
    return {"status": "ok"}
