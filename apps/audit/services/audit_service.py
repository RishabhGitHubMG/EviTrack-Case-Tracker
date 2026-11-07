"""
Audit logging service for EviTrack.
Provides centralized helpers for recording immutable audit trail entries.
"""
from typing import Any
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest


def get_client_ip(request: HttpRequest | None) -> str:
    """
    Extract client IP address from HTTP request headers.
    Handles proxies and load balancers (HTTP_X_FORWARDED_FOR).
    """
    if not request:
        return ''
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or ''


def log_action(
    user: Any,
    action: str,
    obj: Any = None,
    case: Any = None,
    request: HttpRequest | None = None,
    details: dict | None = None,
):
    """
    Create an immutable audit log entry.
    
    Args:
        user: The User instance performing the action (or None for system events).
        action: Dot-notation action string (e.g. 'case.create', 'evidence.upload').
        obj: The target model instance being acted upon (optional).
        case: Case instance associated with this event (optional, inferred from obj if possible).
        request: HttpRequest object to capture IP and User-Agent (optional).
        details: Additional structured JSON details.
    
    Returns:
        AuditLog instance created and hashed.
    """
    from apps.audit.models import AuditLog

    kwargs: dict[str, Any] = {
        'user': user if (user and getattr(user, 'is_authenticated', False)) else None,
        'action': action,
        'details': details or {},
    }

    if obj is not None and hasattr(obj, 'pk') and obj.pk is not None:
        kwargs['content_type'] = ContentType.objects.get_for_model(obj)
        kwargs['object_id'] = str(obj.pk)
        if case is None:
            if hasattr(obj, 'case'):
                kwargs['case'] = getattr(obj, 'case')
            elif obj.__class__.__name__ == 'Case':
                kwargs['case'] = obj

    if case is not None:
        kwargs['case'] = case

    if request is not None:
        kwargs['ip_address'] = get_client_ip(request)
        kwargs['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]

    return AuditLog.objects.create(**kwargs)


def log_audit_event(
    action: str,
    user: Any = None,
    target: Any = None,
    obj: Any = None,
    case: Any = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str = '',
    request: HttpRequest | None = None,
):
    """
    Convenience wrapper for logging immutable audit events with explicit or inferred target object,
    IP address, and client details.
    """
    from apps.audit.models import AuditLog

    target_obj = target or obj
    kwargs: dict[str, Any] = {
        'user': user if (user and getattr(user, 'is_authenticated', False)) else None,
        'action': action,
        'details': details or {},
        'ip_address': ip_address or (get_client_ip(request) if request else ''),
        'user_agent': user_agent or (request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''),
    }

    if target_obj is not None and hasattr(target_obj, 'pk') and target_obj.pk is not None:
        kwargs['content_type'] = ContentType.objects.get_for_model(target_obj)
        kwargs['object_id'] = str(target_obj.pk)
        if case is None:
            if hasattr(target_obj, 'case'):
                kwargs['case'] = getattr(target_obj, 'case')
            elif target_obj.__class__.__name__ == 'Case':
                kwargs['case'] = target_obj

    if case is not None:
        kwargs['case'] = case

    return AuditLog.objects.create(**kwargs)

