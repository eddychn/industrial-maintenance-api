"""
database.py
-----------
Central place where the SQLAlchemy database engine, session factory and the
declarative base class are configured.

Every other module that needs to talk to the database imports from here so that
there is exactly one engine / one configuration for the whole application.

Design notes
------------
* We use SQLite because the assignment asks for a zero-configuration, file-based
  database that is created automatically on first run. In a real factory
  deployment this single line (``SQLALCHEMY_DATABASE_URL``) would be swapped for
  a PostgreSQL / MySQL connection string and *nothing else* in the code base
  would have to change -- that is one of the advantages of using an ORM.
* ``check_same_thread=False`` is required only for SQLite. SQLite by default
  forbids sharing a connection between threads, but FastAPI serves requests from
  a thread pool, so we relax that restriction.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ---------------------------------------------------------------------------
# Connection configuration
# ---------------------------------------------------------------------------
# The database file (``maintenance.db``) is created next to the project root the
# first time the application starts. No manual migration step is required.
#
# The URL can be overridden with the ``DATABASE_URL`` environment variable, which
# is how the Docker setup points the app at a persistent volume (and how you
# would switch to PostgreSQL in production) without any code change.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./maintenance.db")

# ``check_same_thread`` is only valid for SQLite, so only pass it when we are
# actually using SQLite. This keeps the same code working if ``DATABASE_URL`` is
# pointed at PostgreSQL/MySQL instead.
connect_args = (
    {"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)

# The engine is the low-level object that manages the pool of database
# connections. It is created once and reused for the lifetime of the process.
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

# A configured "Session" class. Each request will instantiate its own session
# (see ``get_db`` below) so that database work is isolated per request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models inherit from this Base. SQLAlchemy uses it to keep track of the
# mapping between Python classes and database tables.
Base = declarative_base()


def get_db() -> Session:
    """FastAPI dependency that yields a database session.

    This is the heart of *dependency injection* in this project. Any path
    operation that declares ``db: Session = Depends(get_db)`` will receive a
    fresh session, and the ``finally`` block guarantees the connection is
    returned to the pool even if the request raises an exception.

    Yields:
        Session: an open SQLAlchemy session, closed automatically afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
