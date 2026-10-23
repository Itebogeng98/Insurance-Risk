#!/usr/bin/env bash
set -euo pipefail
# Free instances have no pre-deploy command or interactive shell.
python manage.py migrate --noinput
python manage.py bootstrap_render_admin
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile -
