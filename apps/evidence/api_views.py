"""
REST API views for Evidence verification and metadata retrieval.
"""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.mixins import CaseAccessMixin
from apps.audit.services import log_action
from apps.evidence.models import Evidence, IntegrityCheck
from apps.evidence.services import verify_evidence_integrity


class EvidenceVerifyAPIView(APIView):
    """
    POST /api/v1/evidence/<pk>/verify/
    Cryptographically verify evidence SHA-256 integrity via REST API.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int) -> Response:
        try:
            evidence = Evidence.objects.select_related('case').get(pk=pk)
        except Evidence.DoesNotExist:
            return Response({'error': 'Evidence not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not CaseAccessMixin.user_has_case_access(request.user, evidence.case):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        is_valid, computed_hash = verify_evidence_integrity(evidence)
        result_status = IntegrityCheck.Result.VERIFIED if is_valid else IntegrityCheck.Result.MODIFIED

        check = IntegrityCheck.objects.create(
            evidence=evidence,
            checked_by=request.user,
            result=result_status,
            computed_hash=computed_hash or 'FILE_NOT_FOUND',
            stored_hash=evidence.sha256,
        )

        if not is_valid:
            evidence.status = Evidence.Status.FLAGGED
            evidence.save(update_fields=['status'])

            log_action(
                user=request.user,
                action='evidence.integrity_failure',
                obj=evidence,
                case=evidence.case,
                request=request,
                details={'computed_hash': computed_hash, 'stored_hash': evidence.sha256},
            )
        else:
            log_action(
                user=request.user,
                action='evidence.integrity_verified',
                obj=evidence,
                case=evidence.case,
                request=request,
                details={'computed_hash': computed_hash},
            )

        return Response({
            'evidence_no': evidence.evidence_no,
            'is_valid': is_valid,
            'status': check.result,
            'computed_hash': computed_hash,
            'stored_hash': evidence.sha256,
            'checked_on': check.checked_on.isoformat(),
        }, status=status.HTTP_200_OK)


class EvidenceListAPIView(APIView):
    """
    GET /api/v1/evidence/
    List evidence items accessible to user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request) -> Response:
        accessible_cases = CaseAccessMixin.get_user_cases(request.user)
        qs = Evidence.objects.filter(case__in=accessible_cases).select_related('case')

        case_id = request.query_params.get('case')
        if case_id and case_id.isdigit():
            qs = qs.filter(case_id=int(case_id))

        data = [{
            'id': e.pk,
            'evidence_no': e.evidence_no,
            'title': e.title,
            'case_no': e.case.case_no,
            'mime_type': e.mime_type,
            'file_size': e.file_size,
            'sha256': e.sha256,
            'version': e.version,
            'status': e.status,
            'uploaded_at': e.uploaded_at.isoformat(),
        } for e in qs[:100]]

        return Response({'count': len(data), 'results': data})
