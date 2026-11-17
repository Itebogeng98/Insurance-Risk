# Train the native Kaggle model on Render's free plan

This path trains during the Render **build**, not in the browser or a runtime
worker. It bundles the trained model and evaluation with the deployed application.
No local training is required. No training or application tests were run by the
agent while implementing this path; a successful Render build is still required.

## Set up and deploy

1. Sign in to your Kaggle account and accept the Prudential Life Insurance
   Assessment competition rules where required. Confirm that your intended data
   use complies with those rules. The application does not accept them for you.
   https://www.kaggle.com/competitions/prudential-life-insurance-assessment
2. Generate a Kaggle API token at https://www.kaggle.com/settings/api. Do not
   paste it into chat, source control, slides or the application's upload form.
3. Commit and push all the changed/new files for this feature. Raw CSV files,
   model artifacts and credentials remain excluded from Git.
4. On the existing Render service, set these environment variables:

   ```text
   KAGGLE_BUILD_ENABLED=True
   KAGGLE_API_TOKEN=<your private Kaggle token>
   RENDER_TRAINING_ENABLED=False
   DJANGO_SETTINGS_MODULE=config.render
   ```

5. Keep the build command `bash deploy/render-build.sh` and start command
   `bash deploy/render-start.sh`. Keep your existing database and secret settings.
6. Deploy the latest commit with the new environment settings. Watch the BUILD
   logs for model-fitting progress and `KAGGLE BUILD COMPLETE` with actual metrics.
   Download failure usually means token/access/rule-acceptance problems; a memory
   or timeout failure requires inspecting the Render build logs. Do not repeatedly
   redeploy while training: a new build may cancel the active build.

The official Kaggle CLI (pinned to 2.2.5 for this optional build step) downloads
train.csv into a temporary directory that is removed after training. The API is
used to obtain data; it is not a hosted prediction API. Token values are not logged.

## Demonstrate in the application

1. Log in as an Administrator, for example mcmakwela.
2. Open Model Management, then **Kaggle Analysis**.
3. Confirm the model name, build timestamp, accuracy, macro-F1 and split sizes.
4. Download **Held-out sample**, choose that CSV, then click **Analyse**.
5. Show the predictions and class probabilities produced by the deployed model.

The 20 sample records come from the held-out portion of the genuine dataset,
not synthetic applicants. Target labels and ID are excluded from that sample.
Prediction uploads accept up to 100 rows / 2 MB, and require the native predictor
schema. Optional Id and Response columns are ignored, never used as predictors.
Access is Administrator-only. An audit entry records the action and row count;
uploaded records are not retained or added to the applicant database.

## Important scope distinction

This model appears on the **Kaggle Analysis** page, not as an active applicant
ModelVersion in the database. Its inputs are anonymised Prudential variables.
It cannot score the application's ordinary applicant form or fill its risk
dashboards. This is a functioning research inference path if the build succeeds,
not a completed end-to-end applicant-underwriting integration.

The applicant-model upload/training notice on Model Management remains accurate:
free runtime training is still disabled. Do not set RENDER_TRAINING_ENABLED=True,
approve adapter models or lower production gates to suppress that notice.

This implementation makes the existing benchmark executable on native records;
it does not establish improved accuracy. Candidate selection uses validation
macro-F1 then accuracy; the selected pipeline is refitted on development data and
evaluated on the held-out partition. Identical predictors are deduplicated before
splitting. The dataset has been explored previously, so this is internal evidence,
not an untouched external validation or clinical-risk calibration.

## Persistence, limits and rollback

- The build creates model.joblib, evaluation.json and sample.csv beneath
  risk_engine/ml_models/kaggle_native. They are build outputs, not files created
  by requests on the free runtime filesystem. Routine runtime restarts therefore
  use the same deployed build's files.
- Keep KAGGLE_BUILD_ENABLED=True for builds that need to contain this model.
  Subsequent builds retrain and need API access; disabling it does not promise
  that a previous build's generated files will be carried into a fresh build.
- Training uses build minutes and the build pipeline's CPU/memory budget. No
  completion-time or free-resource guarantee has been measured for this code.
- The full model runs in the free web instance for predictions. The 100-row cap
  limits request work, but runtime memory/latency still need checking on Render.
- A failed build should not replace the prior successful deployment. Use the
  Render deployment logs to distinguish build failures from runtime errors.
- Leave the existing database in place. This build does not migrate records,
  register production model rows or generate applicant data.
- API-token removal stops future downloads; plan for that before rotating it.
  Credentials never belong in a committed .env file.

References checked during implementation:
- https://render.com/docs/build-pipeline
- https://render.com/docs/deploys
- https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md
- https://github.com/Kaggle/kaggle-cli/blob/main/docs/competitions.md
