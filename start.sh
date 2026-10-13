#!/usr/bin/env bash
set -euo pipefail
python manage.py migrate --noinput
python manage.py seed_questions
exec gunicorn raidsite.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers ${WEB_CONCURRENCY:-2} --access-logfile -
