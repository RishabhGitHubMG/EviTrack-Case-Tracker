"""
Custody business logic and service functions.
"""
from django.db import transaction
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import log_audit_event
from apps.custody.models import CustodyEvent
from apps.evidence.models import Evidence
from apps.notifications.models import Notification
from apps.notifications.services import create_notification


@transaction.atomic
def request_transfer(
    evidence: Evidence,
    from_user: User | None,
    to_user: User,
    reason: str,
    ip_address: str | None = None,
    user_agent: str = '',
) -> CustodyEvent:
    """
    Create a new custody transfer request, dispatch an in-app notification to the
    designated recipient, and record an audit log event.
    """
    event = CustodyEvent.objects.create(
        evidence=evidence,
        from_user=from_user,
        to_user=to_user,
        status=CustodyEvent.Status.REQUESTED,
        reason=reason,
    )

    # In-app notification for recipient
    requestor_name = from_user.get_full_name() or from_user.email if from_user else "System"
    try:
        respond_url = reverse('custody:custody_respond', kwargs={'pk': event.pk})
    except Exception:
        respond_url = f"/custody/respond/{event.pk}/"

    create_notification(
        user=to_user,
        message=f"Custody transfer request: Evidence {evidence.evidence_no} ({evidence.title}) from {requestor_name}.",
        link=respond_url,
        notification_type=Notification.NotificationType.INFO,
    )

    # Immutable Audit Log
    log_audit_event(
        action='custody.transfer_requested',
        user=from_user,
        target=event,
        case=evidence.case,
        details={
            'event_id': event.pk,
            'evidence_id': evidence.pk,
            'evidence_no': evidence.evidence_no,
            'from_user_id': from_user.pk if from_user else None,
            'to_user_id': to_user.pk,
            'reason': reason,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return event


@transaction.atomic
def accept_transfer(
    custody_event: CustodyEvent,
    user: User,
    ip_address: str | None = None,
    user_agent: str = '',
) -> CustodyEvent:
    """
    Accept an incoming custody transfer. Updates the status, assigns current holder,
    notifies the sender, and writes to the audit chain.
    """
    now = timezone.now()
    custody_event.status = CustodyEvent.Status.ACCEPTED
    custody_event.resolved_at = now
    custody_event.resolved_by = user
    custody_event.save(update_fields=['status', 'resolved_at', 'resolved_by'])

    evidence = custody_event.evidence
    evidence.current_holder = custody_event.to_user
    evidence.save(update_fields=['current_holder'])

    # Notification to sender
    if custody_event.from_user:
        recipient_name = user.get_full_name() or user.email
        try:
            list_url = reverse('custody:custody_list')
        except Exception:
            list_url = "/custody/"

        create_notification(
            user=custody_event.from_user,
            message=f"Custody transfer of {evidence.evidence_no} was accepted by {recipient_name}.",
            link=list_url,
            notification_type=Notification.NotificationType.SUCCESS,
        )

    # Immutable Audit Log
    log_audit_event(
        action='custody.transfer_accepted',
        user=user,
        target=custody_event,
        case=evidence.case,
        details={
            'event_id': custody_event.pk,
            'evidence_id': evidence.pk,
            'evidence_no': evidence.evidence_no,
            'new_holder_id': custody_event.to_user_id,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return custody_event


@transaction.atomic
def reject_transfer(
    custody_event: CustodyEvent,
    user: User,
    reason: str,
    ip_address: str | None = None,
    user_agent: str = '',
) -> CustodyEvent:
    """
    Reject an incoming custody transfer request with a justification reason.
    """
    now = timezone.now()
    custody_event.status = CustodyEvent.Status.REJECTED
    custody_event.resolved_at = now
    custody_event.resolved_by = user
    if reason:
        custody_event.reason = f"{custody_event.reason}\n\n[Rejection Reason]: {reason}"
    custody_event.save(update_fields=['status', 'resolved_at', 'resolved_by', 'reason'])

    # Notification to sender
    if custody_event.from_user:
        responder_name = user.get_full_name() or user.email
        try:
            list_url = reverse('custody:custody_list')
        except Exception:
            list_url = "/custody/"

        create_notification(
            user=custody_event.from_user,
            message=f"Custody transfer of {custody_event.evidence.evidence_no} was rejected by {responder_name}. Reason: {reason}",
            link=list_url,
            notification_type=Notification.NotificationType.WARNING,
        )

    # Immutable Audit Log
    log_audit_event(
        action='custody.transfer_rejected',
        user=user,
        target=custody_event,
        case=custody_event.evidence.case,
        details={
            'event_id': custody_event.pk,
            'evidence_id': custody_event.evidence_id,
            'evidence_no': custody_event.evidence.evidence_no,
            'rejected_by_id': user.pk,
            'rejection_reason': reason,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return custody_event


def get_custody_timeline(evidence: Evidence) -> QuerySet[CustodyEvent]:
    """
    Return chronological list of CustodyEvents for an evidence item.
    """
    return (
        evidence.custody_events.select_related(
            'from_user', 'to_user', 'resolved_by', 'evidence'
        )
        .order_by('requested_at', 'id')
    )


def get_pending_transfers_for_user(user: User) -> QuerySet[CustodyEvent]:
    """
    Return CustodyEvents where to_user=user and status=Requested.
    """
    return (
        CustodyEvent.objects.filter(
            to_user=user,
            status=CustodyEvent.Status.REQUESTED,
        )
        .select_related('evidence', 'evidence__case', 'from_user')
        .order_by('-requested_at')
    )
