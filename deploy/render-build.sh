#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements-render.txt
if [[ "${KAGGLE_BUILD_ENABLED:-False}" == "True" ]]; then
    python -m pip install kaggle==2.2.5
    python manage.py build_kaggle_model
fi
python manage.py collectstatic --noinput
python manage.py check --deploy
