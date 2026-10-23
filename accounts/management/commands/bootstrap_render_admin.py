"""Optional first-admin provisioning for hosts without an interactive shell."""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create an initial admin from BOOTSTRAP_ADMIN_* variables; never modify existing users.'

    def handle(self, *args, **options):
        username = os.environ.get('BOOTSTRAP_ADMIN_USERNAME', '').strip()
        if not username:
            return
        User = get_user_model()
        existing = User.objects.filter(username=username).first()
        if existing:
            if not existing.is_superuser:
                raise CommandError('Bootstrap username is already in use by a non-superuser.')
            self.stdout.write('Administrator already exists; no account changes made.')
            return
        email = os.environ.get('BOOTSTRAP_ADMIN_EMAIL', '').strip()
        password = os.environ.get('BOOTSTRAP_ADMIN_PASSWORD', '')
        if not email or not password:
            raise CommandError('Set all three BOOTSTRAP_ADMIN_* variables or remove the username.')
        user = User(username=username, email=email, is_staff=True, is_superuser=True)
        try:
            user.full_clean(exclude=['password'])
            validate_password(password, user)
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages)) from exc
        with transaction.atomic():
            user.set_password(password)
            user.save()
            UserProfile.objects.update_or_create(
                user=user, defaults={'role': UserProfile.Role.ADMINISTRATOR},
            )
        self.stdout.write('Administrator created. Remove BOOTSTRAP_ADMIN_* from the host environment.')
