from __future__ import annotations

from django.http import HttpRequest

from .models import AuditLog


def client_ip(request: HttpRequest | None) -> str | None:
    if request is None:
        return None
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def write_audit_log(
    *,
    request: HttpRequest | None = None,
    user=None,
    action: str,
    object_type: str = '',
    object_id: str | int = '',
    detail: str = '',
) -> AuditLog:
    if user is None and request is not None and request.user.is_authenticated:
        user = request.user
    return AuditLog.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        action=action,
        object_type=object_type,
        object_id=str(object_id) if object_id != '' else '',
        detail=detail,
        ip_address=client_ip(request),
    )
