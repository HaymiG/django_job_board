#!/bin/sh
# docker/entrypoint.sh
# ─────────────────────────────────────────────────────────────────────────────
# Container entrypoint script.
#
# This runs BEFORE the main CMD (gunicorn or manage.py).
# It handles one-time boot tasks that must happen after the database is ready:
#
#   1. Wait for PostgreSQL to accept connections (avoids "Connection refused"
#      race condition when the web container starts before the db container).
#   2. Apply any pending database migrations.
#   3. Collect static files into STATIC_ROOT so Whitenoise can serve them.
#   4. Exec the CMD — replacing this shell process with gunicorn (PID 1).
#
# Why `exec "$@"` at the end?
#   `exec` replaces the shell with the given command, making gunicorn PID 1.
#   This ensures Docker signals (SIGTERM on `docker stop`) reach gunicorn
#   directly, allowing graceful shutdown.
# ─────────────────────────────────────────────────────────────────────────────

set -e   # Exit immediately if any command returns a non-zero status.

# ── 1. Wait for PostgreSQL ────────────────────────────────────────────────────
# DB_HOST and DB_PORT are set via environment variables (docker-compose.yml).
# We poll until pg_isready succeeds or we time out after 30 seconds.
if [ "$DB_ENGINE" = "postgres" ]; then
    echo " Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
    timeout=30
    elapsed=0
    until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -q 2>/dev/null; do
        if [ "$elapsed" -ge "$timeout" ]; then
            echo " PostgreSQL did not become ready within ${timeout}s. Aborting."
            exit 1
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    echo " PostgreSQL is ready."
fi

# ── 2. Apply database migrations ──────────────────────────────────────────────
# --no-input: never prompt (safe in automated environments).
echo " Applying database migrations..."
python manage.py migrate --no-input

# ── 3. Collect static files ───────────────────────────────────────────────────
# Whitenoise serves static files directly from STATIC_ROOT in production.
# --no-input: overwrite without prompting.
# --clear: remove stale files from previous builds.
echo " Collecting static files..."
python manage.py collectstatic --no-input --clear

echo " Starting application..."

# ── 4. Hand off to the main CMD ───────────────────────────────────────────────
exec "$@"
