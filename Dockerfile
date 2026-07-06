# syntax=docker/dockerfile:1
#
# Dockerfile -- container image for the Industrial Asset Maintenance Management API.
#
# Uses the official slim Python 3.11 base image to keep the image small, installs
# dependencies in their own layer (so they are cached and only rebuilt when
# requirements.txt changes), and runs the app as a non-root user for safety.

FROM python:3.11-slim AS runtime

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
# PYTHONDONTWRITEBYTECODE: don't litter the image with .pyc files.
# PYTHONUNBUFFERED:        stream logs straight to stdout (good for `docker logs`).
# PIP_NO_CACHE_DIR:        smaller image, we don't need pip's download cache.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---------------------------------------------------------------------------
# Dependencies (cached layer)
# ---------------------------------------------------------------------------
# Copy only requirements first so Docker can reuse this layer whenever the app
# source changes but the dependencies do not.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Application source
# ---------------------------------------------------------------------------
COPY app ./app

# ---------------------------------------------------------------------------
# Non-root user
# ---------------------------------------------------------------------------
# Running as an unprivileged user is a container security best practice. We also
# give it ownership of /app so the SQLite database file can be created/written
# at runtime.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Document the port the app listens on (informational; published via compose/-p).
EXPOSE 8000

# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------
# Hits the lightweight liveness endpoint so orchestrators know when the API is
# ready / healthy. Uses Python (already present) to avoid adding curl/wget.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; \
        sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/health').status == 200 else sys.exit(1)"

# ---------------------------------------------------------------------------
# Start the ASGI server.
# ---------------------------------------------------------------------------
# --host 0.0.0.0 is required so the server is reachable from outside the
# container. No --reload in production.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
