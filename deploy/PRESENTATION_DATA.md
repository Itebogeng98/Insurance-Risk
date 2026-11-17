# Final presentation data: Render

This opt-in batch creates 36 clearly labelled fictional applications, distributed
from 17 August to 17 November 2026 (South African time). Each includes medical,
lifestyle, salary, vehicle history and spending sections. It creates no user
accounts, assessments, predictions, recommendations or fabricated test results.

## Import

1. Take an available database backup/export before changing the live database.
2. Commit and push `accounts/management/commands/seed_presentation_data.py` and
   the updated `deploy/render-start.sh`.
3. Confirm the service uses `bash deploy/render-start.sh` as its start command.
4. Set these temporary environment variables on the Render web service:

   ```text
   PRESENTATION_DATA_BATCH=presentation-2026-11-17-v1
   PRESENTATION_DATA_OWNER=mcmakwela
   ```

5. Deploy the updated commit. Check the logs for
   `Imported 36 synthetic presentation applications.`
6. Remove both temporary environment variables and apply the change.
7. Sign in as `mcmakwela` and search applicants for `Demo`.

No credentials are stored in this command. The owner must already be an active
system Administrator. A wrong owner, identifier collision or validation error
aborts the import and rolls back the entire batch. A completed batch is identified
by its audit entry and skipped on subsequent deployments. If startup fails,
remove the two variables and redeploy before investigating the error.

## Evidence and limits

- Names start with Demo; addresses explain the fictional identity and consent.
- Contacts cannot be used as real contact details; emails use example.invalid.
- IDs satisfy the application's 13-digit format but are not verified identities.
- Only new application `created_at` dates are simulated. Existing data, actual
  update timestamps and audit timestamps are not backdated.
- These are presentation fixtures, not Kaggle rows, historical customers or
  training/validation evidence. Do not use them to claim model accuracy.
- No account links are created. Applicants cannot see these unlinked records;
  administrators can. Underwriters only see records they created, so this batch
  will not populate an underwriter's own list.
- Risk charts may remain empty: scores must come from a genuinely functioning
  model, not this import. Any later assessment has its real execution date.
- This adds no automated cleanup. Retain the batch audit entry and its recorded
  IDs; review references before removing demo data after the presentation.

The import has not been executed locally or on Render by the coding agent.
No tests were run.
