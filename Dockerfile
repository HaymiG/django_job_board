# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Django Job Board
#
# Multi-stage build:
#   Stage 1 (builder) — install Python dependencies into /opt/venv
#   Stage 2 (runtime) — copy only the venv + source code; no build tools
#
# This keeps the final image small (~200 MB) because build tools (gcc, headers)
# are discarded after the wheels are compiled.
#
# Usage (via docker-compose — see docker-compose.yml):
#   docker compose up --build
#
# Usage (standalone):
#   docker build -t jobboard .
#   docker run --env-file .env -p 8000:8000 jobboard
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
# Uses the full Python image so we have compilers available for psycopg.
FROM python:3.12-slim AS builder

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
# so Django logs appear immediately in `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install OS-level build dependencies needed to compile psycopg's C extension.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create an isolated virtual environment — avoids polluting the system Python.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first so Docker can cache this layer.
# If requirements.txt hasn't changed, `pip install` is skipped on rebuild.
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn whitenoise


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
# Slim image — no build tools, just the venv and the application code.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install only the runtime library for libpq (not the -dev headers).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled venv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Create a non-root user for security.
# Running as root inside a container is a known security risk.
RUN groupadd --system django && useradd --system --gid django django

# Set the working directory inside the container.
WORKDIR /app

# Copy the project source code.
COPY --chown=django:django . .

# Create directories that Django writes to at runtime.
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R django:django /app/staticfiles /app/media

# Copy and make the entrypoint script executable.
COPY --chown=django:django docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to the non-root user.
USER django

# Expose the port Gunicorn will listen on.
EXPOSE 8000

# The entrypoint runs migrations + collectstatic, then hands off to CMD.
ENTRYPOINT ["/entrypoint.sh"]

# Default command: Gunicorn serving the Django WSGI app.
# --workers: 2 × CPU cores + 1 is the recommended formula.
# --bind 0.0.0.0:8000: listen on all interfaces inside the container.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-"]
