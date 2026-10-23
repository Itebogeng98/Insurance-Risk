from django.contrib import admin, messages
from django.conf import settings

from .model_versions import activate_model_version
from .models import FeatureContribution, ModelVersion, Recommendation, RiskAssessment, TrainingDataset


class FeatureContributionInline(admin.TabularInline):
    model = FeatureContribution
    extra = 0
    readonly_fields = ('feature', 'label', 'contribution', 'rank')


class RecommendationInline(admin.TabularInline):
    model = Recommendation
    extra = 0


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        'applicant',
        'risk_score',
        'risk_category',
        'confidence',
        'needs_manual_review',
        'model_version',
        'assessed_at',
    )
    list_filter = ('risk_category', 'needs_manual_review')
    search_fields = ('applicant__first_name', 'applicant__last_name', 'applicant__national_id')
    inlines = [FeatureContributionInline, RecommendationInline]


@admin.register(TrainingDataset)
class TrainingDatasetAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return getattr(settings, 'TRAINING_ENABLED', True) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return getattr(settings, 'TRAINING_ENABLED', True) and super().has_change_permission(request, obj)

    list_display = (
        'description',
        'row_count',
        'accepted_rows',
        'rejected_rows',
        'model_version',
        'accuracy',
        'macro_f1',
        'is_active',
        'uploaded_at',
    )
    list_filter = ('is_active',)
    search_fields = ('description', 'model_version')


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    readonly_fields = ('input_contract_verified',)
    list_display = (
        'version_tag',
        'training_date',
        'accuracy',
        'macro_f1',
        'inference_p95_ms',
        'is_active',
    )
    list_filter = ('is_active',)
    search_fields = ('version_tag', 'artifact_path')
    actions = ['activate_model_version']

    @admin.action(description='Activate selected model version for rollback')
    def activate_model_version(self, request, queryset):
        selected = queryset.first()
        if queryset.count() != 1 or selected is None:
            self.message_user(request, 'Select exactly one model version.', level=messages.ERROR)
            return
        try:
            activate_model_version(selected)
        except (OSError, ValueError) as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return
        self.message_user(request, f'{selected.version_tag} is now active.')
