from django.contrib import admin

from .models import (
    Applicant,
    LifestyleHabits,
    MedicalHistory,
    Salary,
    SpendingBehaviour,
    VehicleInsuranceHistory,
)


class MedicalHistoryInline(admin.StackedInline):
    model = MedicalHistory


class LifestyleHabitsInline(admin.StackedInline):
    model = LifestyleHabits


class SalaryInline(admin.StackedInline):
    model = Salary


class VehicleInsuranceHistoryInline(admin.StackedInline):
    model = VehicleInsuranceHistory


class SpendingBehaviourInline(admin.StackedInline):
    model = SpendingBehaviour


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'national_id', 'created_by', 'assigned_underwriter', 'created_at')
    readonly_fields = ('assigned_underwriter',)
    search_fields = ('first_name', 'last_name', 'national_id', 'email')
    inlines = [
        MedicalHistoryInline,
        LifestyleHabitsInline,
        SalaryInline,
        VehicleInsuranceHistoryInline,
        SpendingBehaviourInline,
    ]
