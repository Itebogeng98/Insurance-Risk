from django.conf import settings
from django.db import models

from applicants.models import Applicant


class ModelVersion(models.Model):
    input_contract_verified = models.BooleanField(default=False)
    training_schema = models.PositiveSmallIntegerField(default=1)
    version_tag = models.CharField(max_length=50, unique=True)
    training_date = models.DateTimeField(auto_now_add=True)
    accuracy = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    macro_f1 = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    inference_p95_ms = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    artifact_path = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-training_date']

    def __str__(self) -> str:
        return self.version_tag


class TrainingDataset(models.Model):
    class Status(models.TextChoices):
        STORED = 'STORED', 'Stored'
        QUEUED = 'QUEUED', 'Queued'
        RUNNING = 'RUNNING', 'Training'
        COMPLETE = 'COMPLETE', 'Ready for review'
        FAILED = 'FAILED', 'Failed'

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.STORED)
    error_message = models.CharField(max_length=250, blank=True)
    description = models.CharField(max_length=200)
    csv_file = models.FileField(upload_to='training_datasets/')
    row_count = models.PositiveIntegerField(default=0)
    accepted_rows = models.PositiveIntegerField(default=0)
    rejected_rows = models.PositiveIntegerField(default=0)
    model_version = models.CharField(max_length=80, blank=True)
    accuracy = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    macro_f1 = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    inference_p95_ms = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_datasets',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self) -> str:
        return self.description


class RiskAssessment(models.Model):
    class RiskCategory(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    applicant = models.ForeignKey(
        Applicant, on_delete=models.CASCADE, related_name='risk_assessments'
    )
    risk_score = models.DecimalField(max_digits=5, decimal_places=1)
    risk_category = models.CharField(max_length=10, choices=RiskCategory.choices)
    confidence = models.DecimalField(max_digits=5, decimal_places=3, default=0)
    model_version = models.CharField(max_length=50)
    needs_manual_review = models.BooleanField(default=False)
    assessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assessed_at']

    def __str__(self) -> str:
        return f'{self.applicant} - {self.risk_category} ({self.risk_score})'


class FeatureContribution(models.Model):
    assessment = models.ForeignKey(
        RiskAssessment,
        on_delete=models.CASCADE,
        related_name='feature_contributions',
    )
    feature = models.CharField(max_length=80)
    label = models.CharField(max_length=120)
    contribution = models.DecimalField(max_digits=8, decimal_places=4)
    rank = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['rank']
        constraints = [
            models.UniqueConstraint(
                fields=['assessment', 'rank'],
                name='unique_feature_contribution_rank_per_assessment',
            )
        ]

    def __str__(self) -> str:
        return f'{self.rank}. {self.label} ({self.contribution})'


class Recommendation(models.Model):
    assessment = models.ForeignKey(
        RiskAssessment,
        on_delete=models.CASCADE,
        related_name='recommendations',
    )
    category = models.CharField(max_length=80)
    message = models.TextField()

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return self.message
