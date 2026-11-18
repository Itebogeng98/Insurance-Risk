from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404

from .models import Applicant


def user_role(user) -> str:
    profile = getattr(user, 'profile', None)
    if profile:
        return profile.role
    if user.is_staff or user.is_superuser:
        return 'ADMINISTRATOR'
    return 'UNDERWRITER'


def is_administrator(user) -> bool:
    return user.is_staff or user.is_superuser or user_role(user) == 'ADMINISTRATOR'


def is_applicant(user) -> bool:
    return user_role(user) == 'CUSTOMER'


def can_create_applicants(user) -> bool:
    if not user.is_authenticated or not user.is_active:
        return False
    if is_applicant(user):
        return not Applicant.objects.filter(account=user).exists()
    return True


def can_assess_applicants(user) -> bool:
    return user.is_authenticated and not is_applicant(user)


def application_profile_complete(user) -> bool:
    return user.is_authenticated and all(
        getattr(user, field, '').strip() for field in ('first_name', 'last_name', 'email')
    )


def visible_applicants_for(user) -> QuerySet[Applicant]:
    queryset = Applicant.objects.all()
    if is_administrator(user):
        return queryset
    if user_role(user) == 'CUSTOMER':
        return queryset.filter(account=user)
    return queryset.filter(
        Q(assigned_underwriter=user)
        | Q(assigned_underwriter__isnull=True, created_by=user)
    )


def get_visible_applicant_or_404(user, **lookup) -> Applicant:
    return get_object_or_404(visible_applicants_for(user), **lookup)
