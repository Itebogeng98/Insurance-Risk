# Render Academic Preview

This deployment runs the web application on Render Free with PostgreSQL.
It is not the full training deployment and is not approved for real insurance decisions.
No paid service is declared in `render.yaml`.

## What works and what remains unavailable

- Registration, sign-in, role permissions, applicant capture, dashboards and reports.
- Applicant records and account data live in PostgreSQL, not ephemeral SQLite.
- Static assets are collected at build time and served by WhiteNoise.
- Reports are generated on demand; no public media directory is exposed.
- Dataset uploads, training and model activation are disabled, including API/admin routes.
- New risk scoring remains unavailable until an approved model and its artifact are provisioned.
  No model is bundled, no fake assessments are created, and production validation is not bypassed.
  Reports for existing assessments require those records to be migrated separately.
- Kaggle evaluation stays local. This deployment does not implement Kaggle API synchronization.

Render Free loses local files on restart, redeploy and idle shutdown, has no free
background worker, and sleeps after 15 minutes without incoming traffic.
**The free PostgreSQL database expires after 30 days.** Export data and arrange a
replacement or upgrade before that deadline. This is not indefinite free storage.
Use demonstration records only, not real identity, health or financial information.

## Deploy

1. Put this project in a private GitHub repository accessible to Render. Include
   `render.yaml`, `requirements-render.txt`, `deploy/`, application code, migrations,
   templates and static source files. Do not commit `.env`, credentials, local
   databases, uploads, training CSVs, model artifacts or the virtual environment.
2. In Render choose **New > Blueprint**, connect the repository and select its branch.
   Review that both `assure-risk` and `assure-risk-db` use the **Free** plan before applying.
3. The Blueprint supplies database credentials and generates `SECRET_KEY`.
   `RENDER_EXTERNAL_HOSTNAME` is supplied by Render; settings use that exact host
   for allowed hosts and HTTPS CSRF origins. No wildcard hostname is enabled.
4. Deployment installs the dedicated dependencies and collects static assets.
   Startup applies migrations before launching one Gunicorn worker on `$PORT`.
   Deployment checks may warn about HSTS subdomains/preload; these remain opt-in.
5. Open the generated `https://<service>.onrender.com` address. `/healthz/` returns
   HTTP 200 only when the database query succeeds; it does not certify model readiness.

The existing root `requirements.txt` currently contains unrelated non-package text.
It was deliberately preserved. Render uses `requirements-render.txt`, not that file;
the existing Dockerfile still needs its dependency input corrected before another Docker build.

## Create the first administrator

Free services do not provide an interactive shell. After the initial deployment,
add these secrets in the web service's **Environment** page and redeploy:

| Variable | Value |
| --- | --- |
| `BOOTSTRAP_ADMIN_USERNAME` | A unique, non-public administrator username |
| `BOOTSTRAP_ADMIN_EMAIL` | Your actual email address |
| `BOOTSTRAP_ADMIN_PASSWORD` | A long, unique password; Django validators apply |

Startup creates this account only when it does not already exist. It never resets
an existing account's password or promotes an existing non-superuser. Incomplete
or invalid bootstrap credentials stop startup rather than silently creating a weak account.
After successful creation, **remove all three variables** and redeploy. Sign in at
`/admin/` and assign Underwriter/Administrator profiles as needed. Public registration
continues to create Applicant accounts only. Do not share the administrator password.

## Verify before taking screenshots

- Login and registration load with CSS, icons and images; no missing static assets.
- HTTP redirects to HTTPS; login/session cookies are Secure.
- Applicant cannot create/assess records or view another applicant's data.
- Underwriter cannot manage models or assign privileged roles.
- Administrator can manage accounts and explicitly link an Applicant to their record.
- Upload attempts report unavailability and create no queued jobs.
- Assessment attempts without an approved model fail clearly and save no fabricated result.
- Restart the service and confirm accounts and applicant records remain in PostgreSQL.
- Check `/healthz/`, logs, and the database expiry date; record the expiry reminder.

For a custom domain, add it in Render and set `ALLOWED_HOSTS` to its hostname and
`CSRF_TRUSTED_ORIGINS` to its full HTTPS origin (comma-separated for multiple values).
Keep `SECRET_KEY` stable between deployments. Do not paste credentials into Git or screenshots.

## Full training later

Do not simply enable uploads or add a worker: the current web and worker processes
depend on shared filesystem paths, while Render disks cannot be shared between
services. Full functionality needs shared object storage plus corresponding code
changes, a paid worker, durable database and separately reviewed model provisioning.
Use the local demonstration walkthrough for training and experimental model screenshots.

References: [Render Free](https://render.com/docs/free),
[Django on Render](https://render.com/docs/deploy-django),
[Blueprint specification](https://render.com/docs/blueprint-spec),
[WhiteNoise](https://whitenoise.readthedocs.io/en/stable/django.html).

## Local verification

73 automated tests passed after these changes. Static collection processed 155
source files successfully. A Render-settings smoke check verified HTTPS login,
a Secure CSRF cookie, hashed CSS served with HTTP 200, and HTTP-to-HTTPS redirect.
Migration checks found no pending model changes. The Blueprint parses locally;
actual Render provisioning, Linux runtime startup and hosted PostgreSQL connectivity
still require the first deployment and dashboard verification.
