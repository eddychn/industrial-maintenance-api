# Industrial Asset Maintenance Management API

A production-style **FastAPI** backend for a manufacturing company to manage
factory machines, schedule maintenance, report faults and monitor machine
health. Built to demonstrate industry-standard backend architecture, clean code,
validation, automated tests and API documentation.

### 🚀 Live Demo

The API is deployed on Render — explore it live in your browser:

- **Interactive API docs (Swagger UI):** https://industrial-maintenance-api.onrender.com/docs
- **Alternative docs (ReDoc):** https://industrial-maintenance-api.onrender.com/redoc

> ℹ️ Hosted on Render's free tier, so the first request after a period of
> inactivity may take ~30–50 seconds to wake the service up. Subsequent requests
> are fast.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Architecture](#project-architecture)
4. [Folder & File Guide](#folder--file-guide)
5. [Installation](#installation)
6. [Running the Server](#running-the-server)
7. [Run with Docker](#run-with-docker)
8. [API Endpoints](#api-endpoints)
9. [API Documentation (Swagger)](#api-documentation-swagger)
10. [Postman Collection](#postman-collection)
11. [Running the Tests](#running-the-tests)
12. [Backend Concepts Explained](#backend-concepts-explained)
13. [Future Improvements](#future-improvements)

---

## Features

| # | Module | What it does |
|---|--------|--------------|
| 1 | **Machine Management** | Create, read, update, delete and list factory machines. |
| 2 | **Maintenance Module** | Raise tickets, assign engineers, update status, close tickets. |
| 3 | **Health Monitoring** | Classifies each machine as **Healthy / Warning / Critical** from its health score. |
| 4 | **Analytics Dashboard** | `GET /api/dashboard` returns fleet-wide KPIs. |
| 5 | **Validation** | Pydantic validates every request; invalid data returns `422`. |
| 6 | **API Docs** | Swagger UI (`/docs`) and ReDoc (`/redoc`) generated automatically. |
| 7 | **Database** | SQLite, created automatically on first run. |
| 8 | **Tests** | 23 automated tests (pytest + FastAPI TestClient). |
| 9 | **Postman** | Complete collection covering every endpoint. |

**Business rules built in:**
- Raising a ticket automatically moves the machine into `Maintenance` status.
- Assigning an engineer moves an `Open` ticket to `In Progress`.
- Completing/closing a ticket auto-stamps the completion date.
- Closing a machine's last open ticket returns it to `Running`.

---

## Tech Stack

- **Python 3.11+**
- **FastAPI** — web framework
- **Pydantic v2** — data validation & serialisation
- **SQLAlchemy 2.0 ORM** — database access
- **SQLite** — file-based database
- **Uvicorn** — ASGI server
- **pytest + httpx** — automated testing
- **Swagger UI / OpenAPI** — interactive documentation

---

## Project Architecture

This project follows a **layered (clean) architecture**. Each layer has one job
and only talks to the layer directly beneath it:

```
        HTTP request
             │
             ▼
   ┌───────────────────┐   routers/      →  HTTP concerns: routes, status codes,
   │      Routers      │                     request/response, 404 handling
   └───────────────────┘
             │  calls
             ▼
   ┌───────────────────┐   crud.py       →  all database queries live here
   │    CRUD / Data    │   services/     →  pure business rules (health rules)
   └───────────────────┘
             │  uses
             ▼
   ┌───────────────────┐   models.py     →  SQLAlchemy ORM tables
   │   Models + DB     │   database.py   →  engine, session, get_db dependency
   └───────────────────┘
             │
             ▼
          SQLite

   schemas.py (Pydantic)  →  the API contract, used by routers to validate
                             input and serialise output.
```

**Why this matters:** because database logic is isolated in `crud.py` and the
DB session is provided by dependency injection, we can swap SQLite for
PostgreSQL, or swap the real DB for an in-memory test DB, **without touching the
routers**. The test suite does exactly that.

---

## Folder & File Guide

```
industrial-maintenance-api/
│
├── app/
│   ├── __init__.py           # marks 'app' as a package; holds the version
│   ├── main.py               # entry point: builds the FastAPI app, mounts routers,
│   │                         #   creates DB tables on startup
│   ├── database.py           # SQLAlchemy engine, SessionLocal, Base, get_db() dependency
│   ├── models.py             # ORM models (tables): Machine, MaintenanceTicket + enums
│   ├── schemas.py            # Pydantic schemas: request/response shapes + validation
│   ├── crud.py               # all database Create/Read/Update/Delete functions
│   │
│   ├── routers/              # endpoints grouped by domain
│   │   ├── __init__.py
│   │   ├── machines.py       # /api/machines        (machine CRUD)
│   │   ├── maintenance.py    # /api/maintenance     (tickets, assign, status, close)
│   │   └── health.py         # /api/health/*, /api/dashboard (health + analytics)
│   │
│   └── services/             # pure business logic, easy to unit test
│       ├── __init__.py
│       └── health_service.py # classify_health(): score → Healthy/Warning/Critical
│
├── tests/                    # automated test suite (pytest)
│   ├── __init__.py
│   ├── conftest.py           # fixtures: isolated in-memory test DB + TestClient
│   ├── test_machines.py
│   ├── test_maintenance.py
│   └── test_health_and_dashboard.py
│
├── requirements.txt          # pinned dependencies
├── pytest.ini                # pytest configuration
├── postman_collection.json   # importable Postman collection (every endpoint)
├── .gitignore
└── README.md                 # this file
```

**Why split routers/crud/models/schemas into separate files?**
In a real team, several engineers work on the same service. Small, single-purpose
files reduce merge conflicts, make code review easier, and mean a new joiner can
find "where the database queries live" or "where the request validation lives"
instantly.

---

## Installation

### 1. Prerequisites
- Python 3.11 or newer (`python3 --version`)

### 2. Get the project
```bash
cd industrial-maintenance-api
```

### 3. Create & activate a virtual environment

A **virtual environment** is an isolated Python installation for this project so
its dependencies don't clash with other projects on your machine.

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

You should now see `(.venv)` at the start of your terminal prompt.

### 4. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Running the Server

```bash
uvicorn app.main:app --reload
```

- `app.main:app` = the `app` object inside `app/main.py`.
- `--reload` auto-restarts the server when you edit code (development only).

On first run, the SQLite database file `maintenance.db` is **created
automatically** in the project root — no manual setup required.

The API is now live at **http://127.0.0.1:8000**.

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000/ | Welcome / links |
| http://127.0.0.1:8000/docs | **Swagger UI** (interactive) |
| http://127.0.0.1:8000/redoc | ReDoc documentation |

---

## Run with Docker

If you prefer not to manage a local Python environment, the project ships with a
`Dockerfile` and a `docker-compose.yml` so you can build and run the whole API
with a single command. (Requires **Docker** / Docker Desktop to be installed and
running.)

### Quick start (Docker Compose — recommended)
```bash
docker compose up --build
```
Then open **http://127.0.0.1:8000/docs**. That's it.

Common commands:
```bash
docker compose up -d        # run in the background (detached)
docker compose logs -f api  # follow the application logs
docker compose down         # stop and remove the container
```

### What the setup does
- **Image** — builds from `python:3.11-slim`, installs dependencies in a cached
  layer, and runs the app as a **non-root** user for safety.
- **Port** — publishes container port `8000` to `http://127.0.0.1:8000` on your host.
- **Healthcheck** — Docker polls the `/health` liveness endpoint so
  `docker ps` shows the container as `healthy` once the API is ready.
- **Persistent database** — the SQLite file lives on a named volume (`db_data`),
  so your data **survives container restarts and rebuilds**. Compose sets
  `DATABASE_URL=sqlite:////data/maintenance.db` to point the app at that volume.
  Run `docker compose down -v` if you want to wipe the volume and start fresh.

### Configuring the database location
The app reads the `DATABASE_URL` environment variable (falling back to
`sqlite:///./maintenance.db` when it is not set). Because of this, switching to a
managed PostgreSQL database in production is a **configuration change, not a code
change** — just set, for example,
`DATABASE_URL=postgresql://user:pass@host:5432/maintenance`.

### Build / run without Compose
```bash
docker build -t industrial-maintenance-api .
docker run --rm -p 8000:8000 industrial-maintenance-api
```

> **Port already in use?** If you already have a local `uvicorn` server running
> on port 8000, stop it first (`pkill -f "uvicorn app.main:app"`) or change the
> published port in `docker-compose.yml` (e.g. `"8080:8000"`).

---

## API Endpoints

Base URL: `http://127.0.0.1:8000`

### Machines
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/machines` | Register a new machine (**201**) |
| `GET` | `/api/machines` | List all machines |
| `GET` | `/api/machines/{id}` | Get a machine by ID |
| `PUT` | `/api/machines/{id}` | Update a machine |
| `DELETE` | `/api/machines/{id}` | Delete a machine |

### Maintenance
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/maintenance` | Create a maintenance ticket (**201**) |
| `GET` | `/api/maintenance` | List tickets (filter by `machine_id`, `ticket_status`) |
| `GET` | `/api/maintenance/{id}` | Get a ticket by ID |
| `PATCH` | `/api/maintenance/{id}/assign` | Assign an engineer |
| `PATCH` | `/api/maintenance/{id}/status` | Update ticket status |
| `PUT` | `/api/maintenance/{id}` | Update ticket fields |
| `POST` | `/api/maintenance/{id}/close` | Close a ticket |

### Health & Analytics
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health/machines` | Health condition of every machine |
| `GET` | `/api/health/machines/{id}` | Health condition of one machine |
| `GET` | `/api/dashboard` | Aggregated KPIs (see below) |

**`GET /api/dashboard` returns:**
```json
{
  "total_machines": 12,
  "machines_running": 8,
  "machines_under_maintenance": 2,
  "average_health_score": 76.4,
  "critical_machines": 1,
  "todays_maintenance_count": 3
}
```

### Example: create a machine
```bash
curl -X POST http://127.0.0.1:8000/api/machines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CNC Lathe #4",
    "department": "Machining",
    "manufacturer": "Siemens",
    "installation_date": "2022-05-14",
    "operating_hours": 1200.5,
    "health_score": 85,
    "status": "Running"
  }'
```

---

## API Documentation (Swagger)

FastAPI generates OpenAPI docs **automatically** from the type hints and Pydantic
schemas — there is nothing to write by hand. Start the server and open:

- **Swagger UI:** http://127.0.0.1:8000/docs — try any endpoint live in the browser.
- **ReDoc:** http://127.0.0.1:8000/redoc — clean reference view.
- **Raw spec:** http://127.0.0.1:8000/openapi.json

---

## Postman Collection

1. Open Postman → **Import** → select `postman_collection.json`.
2. The collection variable `base_url` defaults to `http://127.0.0.1:8000`.
3. Run **Create machine** first — its test script saves the new `machine_id` into
   a collection variable. **Create maintenance ticket** does the same for
   `ticket_id`. Every other request then just works.

The collection is organised into four folders (Root, Machines, Maintenance,
Health & Analytics) and covers **all 12 endpoints**.

---

## Running the Tests

```bash
pytest
```

Expected output: `23 passed`.

The tests use an **isolated in-memory SQLite database** (see `tests/conftest.py`)
so they never touch your real `maintenance.db`. This is achieved by overriding
the `get_db` dependency — a practical demonstration of why dependency injection
matters. They cover CRUD, validation errors (`422`), not-found handling (`404`),
the health-classification rules and the dashboard aggregation.

---

## Backend Concepts Explained

This section explains the core concepts the project demonstrates.

### Why FastAPI?
- **Speed:** built on Starlette + async, it is one of the fastest Python frameworks.
- **Automatic validation:** it uses Python type hints + Pydantic to validate
  requests automatically — less boilerplate, fewer bugs.
- **Automatic docs:** interactive Swagger/OpenAPI docs are generated for free.
- **Type safety & editor support:** type hints give autocomplete and catch
  mistakes early.
- **Dependency injection:** a clean, built-in system for supplying things like
  database sessions to endpoints.

### What is a REST API?
**REST** (REpresentational State Transfer) is a style for building web APIs. Key ideas:
- Everything is a **resource** (a machine, a ticket) addressed by a **URL**
  (e.g. `/api/machines/1`).
- You act on resources using standard **HTTP methods** (GET, POST, PUT, DELETE).
- It is **stateless** — each request contains everything needed to process it;
  the server keeps no session between calls.
- Data is exchanged in a standard format, here **JSON**.

### GET vs POST vs PUT vs DELETE
| Method | Purpose | Example | Has body? | Idempotent? |
|--------|---------|---------|-----------|-------------|
| `GET` | **Read** data | `GET /api/machines/1` | No | Yes |
| `POST` | **Create** a new resource | `POST /api/machines` | Yes | No |
| `PUT` | **Update** an existing resource | `PUT /api/machines/1` | Yes | Yes |
| `DELETE` | **Remove** a resource | `DELETE /api/machines/1` | No | Yes |

*Idempotent* = calling it repeatedly has the same effect as calling it once.
(`PATCH`, also used here for partial actions like "assign engineer", updates part
of a resource.)

### Request vs Response
- **Request** = what the client sends: an HTTP method, a URL, optional headers
  (e.g. `Content-Type: application/json`) and an optional **body** (the JSON
  payload).
- **Response** = what the server sends back: a **status code**, headers, and a
  **body** (usually JSON).

Example:
```
Request:   POST /api/machines   body: { "name": "CNC Lathe #4", ... }
Response:  201 Created          body: { "id": 1, "name": "CNC Lathe #4", ... }
```

### HTTP Status Codes
| Code | Meaning | Used in this API when… |
|------|---------|------------------------|
| `200 OK` | Success | GET/PUT/DELETE succeeded |
| `201 Created` | Resource created | a machine or ticket was created |
| `404 Not Found` | Resource doesn't exist | unknown machine/ticket ID |
| `422 Unprocessable Entity` | Validation failed | bad/missing fields in the body |
| `500 Internal Server Error` | Unexpected server error | unhandled exception |

Codes are grouped: `2xx` success, `4xx` client error (you sent something wrong),
`5xx` server error (the server broke).

### JSON Payloads
**JSON** (JavaScript Object Notation) is the text format used to exchange data.
It supports objects `{}`, arrays `[]`, strings, numbers, booleans and `null`:
```json
{
  "name": "CNC Lathe #4",
  "operating_hours": 1200.5,
  "status": "Running",
  "tags": ["machining", "cnc"]
}
```
FastAPI/Pydantic convert incoming JSON into Python objects (validating types
along the way) and convert Python objects back into JSON for the response.

### Dependency Injection in FastAPI
Dependency Injection (DI) means an endpoint **declares what it needs** and
FastAPI **provides it**, instead of the endpoint building it itself.

In this project:
```python
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    ...
```
The endpoint says "I need a database session (`db`)". FastAPI calls `get_db()`,
injects the session, and — thanks to the `yield` in `get_db` — automatically
closes it afterwards. Benefits:
- **Testability:** tests override `get_db` to inject a test database (see
  `conftest.py`) without changing the endpoint.
- **No repetition:** session setup/teardown is written once.
- **Loose coupling:** endpoints don't care *how* the session is created.

### SQLAlchemy Basics
**SQLAlchemy** is an ORM (Object-Relational Mapper): it lets you work with the
database using Python classes instead of hand-written SQL.

- **Engine** (`database.py`) — manages the pool of connections to the database.
- **Model** (`models.py`) — a Python class that maps to a table. `Machine` ↔
  the `machines` table; each attribute (`name`, `status`) is a column.
- **Session** (`get_db`) — your unit of work / conversation with the DB. You
  `add()`, query, and `commit()` through it.
- **Relationship** — `Machine.tickets` links a machine to its tickets so you can
  navigate between them in Python.
- **Query example:**
  ```python
  db.query(Machine).filter(Machine.id == 1).first()
  # ≈ SELECT * FROM machines WHERE id = 1 LIMIT 1;
  ```
Because the ORM abstracts the SQL, moving from SQLite to PostgreSQL is a
one-line change to the connection string.

---

## Future Improvements

Realistic next steps to take this from a portfolio project towards production:

- **Authentication & authorization** — JWT/OAuth2 login so only authorized
  engineers can modify machines; role-based access (viewer vs technician vs admin).
- **Database migrations** — replace `create_all` with **Alembic** so schema
  changes are versioned and safe in production.
- **PostgreSQL** — swap SQLite for PostgreSQL for concurrency and scale.
- **Async database access** — move to SQLAlchemy's async engine for higher
  throughput under load.
- **Pagination metadata** — return total counts and next/prev links on list
  endpoints.
- **Structured logging & monitoring** — request logging, health/metrics endpoints
  for Prometheus, error tracking (Sentry).
- **Predictive maintenance** — ingest live sensor/operating-hours data and use it
  to forecast the health score and auto-raise tickets before failure.
- **Background jobs** — Celery / APScheduler to send reminders for scheduled
  maintenance.
- **CI/CD pipeline** — a GitHub Actions workflow that runs the test suite and
  builds the Docker image on every push. (Containerisation itself is already
  done — see [Run with Docker](#run-with-docker).)
- **Rate limiting & CORS configuration** for safe public exposure.

---

## Screenshots

> Interactive API documentation (Swagger UI) available at `http://127.0.0.1:8000/docs`
> once the server is running.

| View | Description |
|------|-------------|
| **Swagger UI** | Full interactive API docs — try every endpoint live. |
| **Dashboard response** | Aggregated KPI summary from `GET /api/dashboard`. |
| **Health monitoring** | Healthy / Warning / Critical classification per machine. |

_To add images: run the app, take screenshots of `/docs`, save them under a
`docs/screenshots/` folder, and embed them here, e.g.:_

```markdown
![Swagger UI](docs/screenshots/swagger-ui.png)
![Dashboard](docs/screenshots/dashboard.png)
```

---

## Author

**Aditya Chauhan**

- GitHub: [@eddychn](https://github.com/eddychn)
- Email: adtchauhan123@gmail.com

Built as a backend engineering portfolio project to demonstrate production-style
API development with FastAPI.

---

*Built as a demonstration of industry-standard backend engineering practices:
layered architecture, type hints, validation, dependency injection, automated
testing and clear documentation.*
