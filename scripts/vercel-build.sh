#!/usr/bin/env bash
set -euo pipefail

export DJANGO_SETTINGS_MODULE=ahoum.settings.production

python manage.py collectstatic --noinput
python manage.py migrate --noinput

if [ "${SEED_ON_DEPLOY:-}" = "1" ]; then
  python seed.py
fi
