from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Applicant'
        UNDERWRITER = 'UNDERWRITER', 'Underwriter'
        ADMINISTRATOR = 'ADMINISTRATOR', 'Administrator'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.UNDERWRITER,
    )

    def __str__(self) -> str:
        return f'{self.user} ({self.get_role_display()})'


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCESS = 'LOGIN_SUCCESS', 'Login success'
        LOGIN_FAILURE = 'LOGIN_FAILURE', 'Login failure'
        DATA_ACCESS = 'DATA_ACCESS', 'Data access'
        DATA_CHANGE = 'DATA_CHANGE', 'Data change'
        RISK_ASSESSMENT = 'RISK_ASSESSMENT', 'Risk assessment'
        MODEL_TRAINING = 'MODEL_TRAINING', 'Model training'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=30, choices=Action.choices)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    detail = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.action} by {self.user or "anonymous"} at {self.created_at:%Y-%m-%d %H:%M}'
