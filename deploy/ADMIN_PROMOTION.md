# Promote an existing Render account

Only a trusted host operator should perform this procedure. It grants full
application Administrator and Django superuser access, not just dashboard access.
It does not create accounts, reset passwords, or enable disabled accounts.

1. Commit and push the promotion command and updated `deploy/render-start.sh`.
2. In the Render web service environment, temporarily set
   `PROMOTE_ADMIN_USERNAME` to the exact existing username, for example `MC@2002`.
3. Remove obsolete `BOOTSTRAP_ADMIN_*` variables if first-admin provisioning is
   no longer needed. They are for creating an initial account, not promotion.
4. Deploy the updated code. The start command must be
   `bash deploy/render-start.sh` for automatic promotion to run.
5. Check deployment logs for `Administrator promotion complete.` or the message
   confirming the account already has all three permissions. Missing or disabled
   accounts cause startup to fail without creating or enabling an account. Correct
   or remove the variable and redeploy if that happens.
6. Immediately remove `PROMOTE_ADMIN_USERNAME` and apply the environment change.
   The database permissions persist. Leaving it set would re-grant permissions
   after a later demotion and could affect a replacement account with that name.
7. Log out, then sign in at `/admin/` using that username and its existing password.

Promotion is transactional and creates an audit entry only when permissions
change. It is not exposed through public registration or a web endpoint.
No production account is modified merely by editing these local files.
