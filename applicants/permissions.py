from django.db.models import QuerySet
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
    return user.is_authenticated and not is_applicant(user)


def can_assess_applicants(user) -> bool:
    return user.is_authenticated and not is_applicant(user)


def visible_applicants_for(user) -> QuerySet[Applicant]:
    queryset = Applicant.objects.all()
    if is_administrator(user):
        return queryset
    if user_role(user) == 'CUSTOMER':
        return queryset.filter(account=user)
    return queryset.filter(created_by=user)


def get_visible_applicant_or_404(user, **lookup) -> Applicant:
    return get_object_or_404(visible_applicants_for(user), **lookup)
