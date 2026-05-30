#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Seeding sample data (safe to re-run)..."
python seed.py

exec "$@"
