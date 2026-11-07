"""
Celery asynchronous tasks for Evidence processing and bulk integrity verifications.
"""
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.notifications.services import create_notification

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def verify_case_evidence_task(self, case_id: int, user_id: int | None = None) -> dict:
    """
    Asynchronously verify cryptographic integrity for all evidence items belonging to a case.
    """
    from apps.audit.services import log_action
    from apps.cases.models import Case
    from apps.evidence.models import Evidence, IntegrityCheck
    from apps.evidence.services import verify_evidence_integrity
    from apps.notifications.models import Notification

    User = get_user_model()
    user = User.objects.filter(pk=user_id).first() if user_id else None

    case = Case.objects.filter(pk=case_id).first()
    if not case:
        logger.error("Bulk verify failed: Case %s not found.", case_id)
        return {'status': 'error', 'message': 'Case not found'}

    evidence_qs = case.evidence_items.all()
    total = evidence_qs.count()
    verified_count = 0
    failed_count = 0
    results = []

    for evidence in evidence_qs:
        is_valid, computed_hash = verify_evidence_integrity(evidence)
        result_status = IntegrityCheck.Result.VERIFIED if is_valid else IntegrityCheck.Result.MODIFIED
        
        check = IntegrityCheck.objects.create(
            evidence=evidence,
            checked_by=user,
            result=result_status,
            computed_hash=computed_hash or 'FILE_NOT_FOUND',
            stored_hash=evidence.sha256,
            checked_on=timezone.now(),
        )

        if not is_valid:
            failed_count += 1
            evidence.status = Evidence.Status.FLAGGED
            evidence.save(update_fields=['status'])

            # Send critical alert notification
            if user:
                create_notification(
                    user=user,
                    message=f"INTEGRITY BREACH: Evidence {evidence.evidence_no} failed SHA-256 verification in Case {case.case_no}.",
                    link=reverse('evidence:evidence_detail', kwargs={'pk': evidence.pk}),
                    notification_type=Notification.NotificationType.DANGER,
                )

            log_action(
                user=user,
                action='evidence.integrity_failure',
                obj=evidence,
                case=case,
                details={
                    'computed_hash': computed_hash,
                    'stored_hash': evidence.sha256,
                    'check_id': check.pk,
                },
            )
        else:
            verified_count += 1
            log_action(
                user=user,
                action='evidence.integrity_verified',
                obj=evidence,
                case=case,
                details={'computed_hash': computed_hash, 'check_id': check.pk},
            )

        results.append({
            'evidence_no': evidence.evidence_no,
            'is_valid': is_valid,
            'computed_hash': computed_hash,
        })

    logger.info(
        "Bulk verification completed for Case %s: %s verified, %s failed.",
        case.case_no, verified_count, failed_count
    )

    return {
        'status': 'completed',
        'case_no': case.case_no,
        'total': total,
        'verified': verified_count,
        'failed': failed_count,
        'results': results,
    }
