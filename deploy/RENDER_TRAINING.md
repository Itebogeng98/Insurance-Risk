# Enable hosted training on the existing Render service

Status: implementation prepared; not deployed or runtime-tested by the agent.
No tests or training were run. These changes do not upgrade your service, attach
a disk, provide a dataset, approve a model or purchase hosting automatically.

## Hosting requirements

The current pipeline saves CSV and joblib files to the filesystem. The supported
configuration is one paid web service instance with one persistent disk mounted
at `/var/data`. Web and training run as separate supervised processes on that
same instance. They share PostgreSQL and the mounted disk. Do not add a separate
Render worker expecting it to read this disk: disks are not shared across services.

Training consumes extra CPU and memory alongside the web process. Choose memory
capacity based on the uploaded dataset; no minimum has been benchmarked here.
A low-memory instance may be killed during pandas processing or model fitting.
Train before the presentation, not during a redeploy or an important live step.

The free web-only deployment remains the default in render.yaml. Merely setting
an environment variable on a free service is not a supported training deployment.
No paid resources are provisioned by the repository changes.

## Deploy in place

1. Back up/export the existing database; do not create a replacement service or
   database. Confirm that the current database is healthy and not nearing expiry.
2. In the existing web service, choose an appropriate paid compute instance and
   attach a persistent disk with mount path `/var/data` and sufficient capacity
   for uploaded datasets, models and evidence. These are billable resources.
3. Push the changes to config/render.py, deploy/render-start.sh,
   deploy/render_runtime.py and the risk_engine files changed for this feature.
4. Keep `DJANGO_SETTINGS_MODULE=config.render`, the existing database settings,
   and start command `bash deploy/render-start.sh`.
5. Set `RENDER_TRAINING_ENABLED=True` exactly, then deploy the updated commit.
   Do not set REQUIRE_VALIDATED_MODEL=False or lower the acceptance thresholds.
6. Check logs for `Training worker ready` and successful Gunicorn startup. A
   missing mount causes startup to fail explicitly instead of accepting files
   that disappear. Removing RENDER_TRAINING_ENABLED restores web-only operation.
7. Sign in as an Administrator, open Model Management and upload a labelled CSV.
   Refresh to follow Queued, Training, Ready for review or Failed status.

If using Blueprint sync, explicitly update the existing service's plan and disk
configuration there too before applying it. The checked-in free blueprint is
not a specification for this opt-in paid setup; do not blindly resync it over
your upgraded service. The database is not moved by these code changes.

## Training, review and activation

- Uploading a dataset does not create applicants. It creates a training job.
- The applicant CSV template defines the live-input-compatible schema. Provide
  authorised measured records with genuine independent HUMAN_UNDERWRITING labels.
- Prudential CSV uploads still create adapter-based candidates, but those cannot
  be approved for live applicant scoring. The offline Kaggle benchmark is a
  different evaluation path and is not silently substituted for this model.
- Training stores an immutable version file and JSON evaluation evidence on disk.
- For an applicant-schema candidate, open Review on Model Management. Review the
  actual data provenance, labelling and input mapping, enter review notes, and
  confirm only if the statement is true. Approval is logged against your account.
- Review checks the source checksum and evidence, plus the existing production
  quality gates (accuracy >= 0.85 and macro-F1 >= 0.80). A checkbox cannot make
  synthetic labels genuine or an unsuitable model valid.
- After approval, click Activate. Activation is logged. Then run an assessment
  on a complete applicant profile and open the resulting report.
- The model remains experimental decision support; internal holdout performance
  and a human input review are not independent external or clinical validation.

There is currently no supplied, verified applicant-labelled dataset or confirmed
approved model. A hosting upgrade alone therefore cannot guarantee scoring will
be ready. Do not fabricate labels or approval evidence to get through the gate.

## Worker lifecycle and operational checks

The supervisor stops the service if either child exits, and forwards shutdown
signals to both process groups. On the next startup, the single worker marks
interrupted RUNNING jobs Failed with a retry instruction. Queued jobs are retained
in PostgreSQL and picked up normally. Re-upload failed datasets to retry.
Do not run a second worker with --recover-interrupted while another is training.

Only paths under `/var/data` survive restarts. Earlier ephemeral uploads/artifacts
are not migrated automatically. Re-upload missing CSVs and retrain, or have an
operator securely migrate genuine artifacts and update their paths. Preserve
separate backups for the disk and database. Raw training files must remain private;
do not expose the media directory through a public URL.

The user must verify on Render: login, authorised upload, completed training,
review rejection/approval, activation, scoring, PDF output, role isolation and
persistence after restart. These are required checks, not results already obtained.

Official references checked during implementation:
- https://render.com/docs/disks
- https://render.com/docs/free
