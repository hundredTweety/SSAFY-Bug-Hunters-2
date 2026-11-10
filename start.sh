#!/usr/bin/env bash
set -euo pipefail
python manage.py migrate --noinput
# Purge expired Django auth sessions on deployments; no live raid data is touched.
python manage.py clearsessions
python manage.py seed_questions
python manage.py bootstrap_admin
exec gunicorn raidsite.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers ${WEB_CONCURRENCY:-2} --access-logfile -
