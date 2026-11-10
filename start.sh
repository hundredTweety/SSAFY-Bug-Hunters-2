#!/usr/bin/env bash
set -euo pipefail
# One Django process for migrate, clearsessions, seed_questions and bootstrap_admin.
# Booting Django once (instead of four times) shortens free-tier cold starts.
python manage.py prepare_runtime
exec gunicorn raidsite.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers ${WEB_CONCURRENCY:-2} --access-logfile -
