"""Explicit operator-controlled promotion of an existing hosted account."""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import AuditLog, UserProfile


class Command(BaseCommand):
    help = 'Promote an existing active user named by PROMOTE_ADMIN_USERNAME.'

    def handle(self, *args, **options):
        username = os.environ.get('PROMOTE_ADMIN_USERNAME', '').strip()
        if not username:
            return

        User = get_user_model()
        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(username=username)
            except User.DoesNotExist as exc:
                raise CommandError(
                    'Promotion account not found. Check PROMOTE_ADMIN_USERNAME; '
                    'no account was created.'
                ) from exc
            if not user.is_active or not user.has_usable_password():
                raise CommandError(
                    'Promotion requires an active account with a usable password. '
                    'No account changes made.'
                )

            profile, _ = UserProfile.objects.get_or_create(user=user)
            changed = (
                not user.is_staff
                or not user.is_superuser
                or profile.role != UserProfile.Role.ADMINISTRATOR
            )
            if changed:
                user.is_staff = True
                user.is_superuser = True
                user.save(update_fields=['is_staff', 'is_superuser'])
                profile.role = UserProfile.Role.ADMINISTRATOR
                profile.save(update_fields=['role'])
                AuditLog.objects.create(
                    user=None,
                    action=AuditLog.Action.DATA_CHANGE,
                    object_type='User',
                    object_id=str(user.pk),
                    detail=(
                        'Host operator promoted existing account to Administrator '
                        'with staff and superuser access via PROMOTE_ADMIN_USERNAME. '
                        'Password unchanged.'
                    ),
                )

        self.stdout.write(self.style.SUCCESS(
            'Administrator promotion complete.' if changed
            else 'Account already has Administrator, staff and superuser access.'
        ))
        self.stdout.write(
            'Remove PROMOTE_ADMIN_USERNAME from the host environment now. '
            'The existing password is unchanged.'
        )
