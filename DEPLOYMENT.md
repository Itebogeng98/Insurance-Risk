# Deployment

For the Render free-tier academic web preview, use [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md).
The Docker instructions below describe the separate full-stack deployment.

For the local academic demonstration, follow DEMONSTRATION_WALKTHROUGH.md.
`ACADEMIC_DEMO=True` identifies experimental outputs in the UI and exported PDFs;
it does not disable production model-validation gates.

Use a Linux Docker host with a domain pointing to it. Production uses PostgreSQL,
Gunicorn behind Caddy HTTPS, and a separate database-backed training worker.
The Python image matches the local 3.14 runtime; pinned NumPy/SciPy require 3.12+.

Configure `.env.production` using `.env.production.example`, with real domain and
random secrets. Never commit credentials. Run these commands from the project:

```sh
docker compose --env-file .env.production build
docker compose --env-file .env.production up -d db
docker compose --env-file .env.production run --rm web python manage.py migrate
docker compose --env-file .env.production run --rm web python manage.py collectstatic --noinput
docker compose --env-file .env.production run --rm web python manage.py check --deploy
docker compose --env-file .env.production run --rm web python manage.py createsuperuser
docker compose --env-file .env.production up -d
```

Only Caddy exposes ports. Do not expose Gunicorn directly: production trusts the
HTTPS forwarding header overwritten by Caddy. Uploads are private and are not
served by the proxy. Database, static files, uploads, models and certificates
use persistent volumes. Restrict host access and back up the database and
application volume together; test restoration before accepting real records.
Deployment checks may report W005/W021: HSTS subdomain coverage and preload are
intentionally opt-in until the domain owner confirms every subdomain supports HTTPS.
Set SECURE_HSTS_INCLUDE_SUBDOMAINS=True and SECURE_HSTS_PRELOAD=True only then.

## Account access

Public registration creates Applicants only. An administrator assigns Underwriter
or Administrator roles through user profiles in Django admin. To grant an Applicant
access to an existing record, verify ownership and set the record's `account` field
in Django admin. Migration deliberately leaves existing records unlinked: an email
match is not proof of identity. Editing email no longer changes record access.

Session-authenticated API writes and API login require a CSRF token. Obtain it from
the login page and send its value in `X-CSRFToken` with the matching cookie. Authenticated
Bearer API requests do not use session cookies and can omit CSRF. Disabled accounts
cannot use previously issued tokens.

## Training

The preferred path is a labelled applicant CSV matching the live form. Download
the empty template on `/risk/models/` and follow
`evaluation/APPLICANT_DATA_CONTRACT.md`. The worker validates actual inputs,
uses supplied human underwriting labels, calculates age at observation, and saves
an inactive schema-3 candidate with a JSON evidence file. Missing credit scores
are handled by the fitted imputer. No Kaggle or synthetic rows are mixed into this
path. Schema validation does not verify provenance; production approval stays blocked
until the input contract and outcomes have been independently reviewed.

For demonstration-only training, upload a Prudential CSV including `Response`.
The file must be at most 50 MB, contain 30-200,000 rows, and include at least five
examples per mapped class (Response 1-2 HIGH, 3-5 MEDIUM, 6-8 LOW). Required columns:
Ins_Age, Ht, Wt, BMI, Employment_Info_1, Employment_Info_2, Employment_Info_6,
InsuredInfo_1, Medical_History_1, Response. Numeric missing values are allowed
except Response, but required input columns must have some observations.

The upload queues a durable database record. The worker trains on that file alone,
records metrics and saves an inactive candidate. Review metrics before activation.
Failed jobs expose a generic error in the model page; details are in worker logs.
After a worker crash, inspect logs and set stranded RUNNING jobs to QUEUED in admin
only once the original worker is stopped. Run just one worker initially.

For local development, run the worker in a separate terminal:

```powershell
venv\Scripts\python.exe manage.py process_training_jobs
```

The command `train_risk_model --csv-path PATH` also trains an inactive candidate.
Explicit `--activate` activates it. Legacy models are blocked in production until
retrained. Model caches are keyed by artifact path and modification time, so each
web process observes a changed active version.

Production also requires accuracy >= 0.85 and macro F1 >= 0.80 for activation and
inference. These match the project acceptance criteria, but are not a substitute
for independent model validation. The corrected full Kaggle run measured accuracy
0.608, macro F1 0.514 and p95 inference 19.62 ms, on 59,381 source rows with 11,877
held-out rows. It remains inactive and does not meet the production gate.

The mapping audit additionally found unsupported semantic conversions in the
demonstration adapter. Production now requires `input_contract_verified=True`;
existing versions are unverified and the admin cannot override this field. A new
native-feature benchmark achieved 75.06% accuracy / 0.6718 macro F1, but cannot
consume live form inputs and is not registered for activation. See
`evaluation/RESULTS.md` and `evaluation/MAPPING_AUDIT.md` before choosing a dataset
or making any deployment-readiness claim.

The old accuracy/F1 figures in assignment documents must not be used as evidence
for corrected models: financial and vehicle inputs previously leaked Response.
The corrected transform uses label-independent defaults for unavailable fields.
Other mappings remain project approximations, not validated insurer measurements.
Review independent evaluation and suitability before using this for real decisions.

## Release verification

Run tests, deploy checks, and migration checks. On staging, verify HTTPS, static
assets, all three roles, cross-account denial, PDF reports, CSV validation, queued
training, model activation across workers, restart persistence and backup restore.
Automated unit tests alone do not establish production readiness.
