# Run locally on Windows

From this folder, run `powershell -ExecutionPolicy Bypass -File .\start.ps1`,
then open http://127.0.0.1:8000. Keep that terminal open.
For uploaded training jobs, open another terminal and run
`powershell -ExecutionPolicy Bypass -File .\start-worker.ps1`.
The database-backed worker does not require Redis.

Create a private `.env` before running migrations. Set `SECRET_KEY` to a securely
generated random value, `DEBUG=True`, `ACADEMIC_DEMO=True`, and
`ALLOWED_HOSTS=localhost,127.0.0.1`. For a self-contained local database set
`DB_ENGINE=sqlite`; data is saved in `db.sqlite3`. For MySQL set `DB_ENGINE=mysql`
and configure `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT` for your
own server. Full Django backend names are also supported.
Never commit or share `.env`. Local administrator credentials, when generated
during setup, are stored there as `LOCAL_ADMIN_USERNAME` / `LOCAL_ADMIN_PASSWORD`.
Databases and accounts are local and are not included in a Git clone; create
your own administrator after migrating.

The full Prudential training source is already supplied at
`etl/raw_data/train.csv`; it does not need downloading again. It is demonstration
data with approximate mappings to the applicant form, not validated underwriting
data. The local scoring model is experimental. Production validation requirements
remain as documented in `DEPLOYMENT.md`.
The native Kaggle analysis model is stored separately under
`risk_engine/ml_models/kaggle_native/`; its `sample.csv` can be used to try native
CSV analysis. To rebuild it without Kaggle credentials:

```powershell
$env:KAGGLE_BUILD_CSV_PATH = 'etl/raw_data/train.csv'
.\.venv\Scripts\python.exe manage.py build_kaggle_model
```

To recreate the Python environment using Python 3.14:

```powershell
python -m venv .venv
$env:DEBUG = 'True'
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py train_risk_model --csv-path etl/raw_data/train.csv --activate
```

Use `createsuperuser` only if you need another administrator. To run the existing
automated tests, set `$env:DEBUG = 'True'` and run
`.\.venv\Scripts\python.exe manage.py test --settings=config.test_settings`.
The launch scripts set this too because this machine has a system `DEBUG=release`
variable that otherwise takes precedence over `.env`.
For hosting, use the separate deployment instructions; `start.ps1` runs a local
development server only.
