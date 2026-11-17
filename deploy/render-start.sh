#!/usr/bin/env bash
set -euo pipefail
# Free instances have no pre-deploy command or interactive shell.
python manage.py migrate --noinput
python manage.py promote_render_admin
python manage.py bootstrap_render_admin
python manage.py seed_presentation_data
exec python deploy/render_runtime.py
