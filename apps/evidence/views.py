"""
Views for Evidence Vault: listing, intake, detail, verification, preview, download, and QR codes.
"""
import mimetypes
import os
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView

from apps.accounts.mixins import ReadOnlyMixin, check_case_access, get_user_accessible_cases
from apps.audit.services import log_action
from apps.cases.models import Case
from apps.custody.models import CustodyEvent
from apps.evidence.forms import EvidenceUpdateForm, EvidenceUploadForm
from apps.evidence.models import Evidence, IntegrityCheck, Tag
from apps.evidence.services import (
    compute_sha256,
    generate_qr_label,
    get_evidence_file_path,
    store_evidence_file,
    verify_evidence_integrity,
)
from apps.notifications.models import Notification
from apps.notifications.services import create_notification


class EvidenceListView(LoginRequiredMixin, ListView):
    """
    Searchable, filterable list of evidence items accessible to the authenticated user.
    Supports both Table/List view and Grid Card view.
    """
    model = Evidence
    template_name = 'evidence/evidence_list.html'
    context_object_name = 'evidence_list'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        accessible_cases = get_user_accessible_cases(user)

        qs = Evidence.objects.filter(case__in=accessible_cases).select_related(
            'case', 'uploaded_by', 'current_holder'
        ).prefetch_related('tags')

        # Filters
        case_id = self.request.GET.get('case')
        if case_id and case_id.isdigit():
            qs = qs.filter(case_id=int(case_id))

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        tag_name = self.request.GET.get('tag')
        if tag_name:
            qs = qs.filter(tags__name__iexact=tag_name)

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(evidence_no__icontains=q) |
                Q(title__icontains=q) |
                Q(sha256__icontains=q) |
                Q(original_filename__icontains=q)
            )

        # Show latest versions by default unless all requested
        if self.request.GET.get('all_versions') != '1':
            qs = qs.filter(is_latest_version=True)

        return qs.order_by('-uploaded_at')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        accessible_cases = get_user_accessible_cases(user)

        context['cases'] = accessible_cases.order_by('case_no')
        context['all_tags'] = Tag.objects.filter(evidence_items__case__in=accessible_cases).distinct().order_by('name')[:30]
        context['status_choices'] = Evidence.Status.choices
        context['view_mode'] = self.request.GET.get('view', 'list')
        context['selected_case'] = self.request.GET.get('case', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_tag'] = self.request.GET.get('tag', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['is_reviewer'] = getattr(user, 'is_reviewer', False)
        return context


class EvidenceUploadView(LoginRequiredMixin, ReadOnlyMixin, View):
    """
    Intake and upload view for lodging digital evidence files into the secure vault.
    Supports single or multiple file uploads, automatic SHA-256 calculation,
    initial Chain of Custody logging, and versioning.
    """

    def get(self, request: HttpRequest, case_id: int | None = None) -> HttpResponse:
        case = None
        if case_id:
            case = get_object_or_404(Case, pk=case_id)
            if not check_case_access(request.user, case):
                raise PermissionDenied("You do not have permission to upload evidence for this case.")

        accessible_cases = get_user_accessible_cases(request.user)
        form = EvidenceUploadForm()

        parent_id = request.GET.get('parent')
        parent_evidence = None
        if parent_id and parent_id.isdigit():
            parent_evidence = Evidence.objects.filter(pk=int(parent_id), case=case).first()

        return render(
            request,
            'evidence/evidence_upload.html',
            {
                'form': form,
                'case': case,
                'cases': accessible_cases,
                'parent_evidence': parent_evidence,
            },
        )

    def post(self, request: HttpRequest, case_id: int | None = None) -> HttpResponse:
        target_case_id = case_id or request.POST.get('case_id')
        if not target_case_id:
            messages.error(request, "Please designate a case for this evidence upload.")
            return redirect('evidence:evidence_list')

        case = get_object_or_404(Case, pk=target_case_id)
        if not check_case_access(request.user, case):
            raise PermissionDenied("You do not have permission to upload evidence for this case.")

        # Check for multiple files vs single file
        files = request.FILES.getlist('file')
        if not files:
            messages.error(request, "No files were selected for upload.")
            return redirect(request.path)

        parent_id = request.POST.get('parent_id')
        parent_evidence = Evidence.objects.filter(pk=parent_id, case=case).first() if parent_id else None

        title_input = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        tags_raw = request.POST.get('tags_input', '').strip()
        tag_names = [t.strip().lower() for t in tags_raw.split(',') if t.strip()]

        created_items = []

        for uploaded_file in files:
            # Validate individual file using form validator
            dummy_form = EvidenceUploadForm(
                {'title': title_input or uploaded_file.name, 'description': description},
                {'file': uploaded_file},
            )
            if not dummy_form.is_valid():
                err_msg = "; ".join([e.as_text() for e in dummy_form.errors.values()])
                messages.error(request, f"Error uploading {uploaded_file.name}: {err_msg}")
                continue

            # 1. Compute SHA-256 hash
            sha256_digest = compute_sha256(uploaded_file)

            # 2. Store file securely outside web root
            relative_path = store_evidence_file(uploaded_file, case)

            # Determine mime type
            content_type = getattr(uploaded_file, 'content_type', '')
            if not content_type or content_type == 'application/octet-stream':
                guessed, _ = mimetypes.guess_type(uploaded_file.name)
                content_type = guessed or 'application/octet-stream'

            # 3. Create Evidence Record
            version_num = (parent_evidence.version + 1) if parent_evidence else 1
            item_title = title_input if (len(files) == 1 and title_input) else uploaded_file.name

            evidence = Evidence.objects.create(
                case=case,
                title=item_title,
                description=description,
                file_path=relative_path,
                original_filename=uploaded_file.name,
                mime_type=content_type[:100],
                file_size=uploaded_file.size,
                sha256=sha256_digest,
                version=version_num,
                parent=parent_evidence,
                uploaded_by=request.user,
                current_holder=request.user,
                status=Evidence.Status.ACTIVE,
                is_latest_version=True,
            )

            # Handle tags
            for t_name in tag_names:
                tag_obj, _ = Tag.objects.get_or_create(name=t_name)
                evidence.tags.add(tag_obj)

            # 4. Create Initial Chain of Custody Entry
            CustodyEvent.objects.create(
                evidence=evidence,
                from_user=None,
                to_user=request.user,
                status=CustodyEvent.Status.ACCEPTED,
                reason="Initial intake, verification, and cryptographic vault deposit.",
                resolved_at=timezone.now(),
                resolved_by=request.user,
            )

            # 5. Create Audit Log
            log_action(
                user=request.user,
                action='evidence.upload',
                obj=evidence,
                case=case,
                request=request,
                details={
                    'evidence_no': evidence.evidence_no,
                    'original_filename': evidence.original_filename,
                    'file_size': evidence.file_size,
                    'sha256': evidence.sha256,
                    'version': evidence.version,
                },
            )

            created_items.append(evidence)

        if created_items:
            if len(created_items) == 1:
                item = created_items[0]
                messages.success(request, f"Evidence {item.evidence_no} deposited successfully with SHA-256 verified.")
                return redirect('evidence:evidence_detail', pk=item.pk)
            else:
                messages.success(request, f"Successfully lodged {len(created_items)} evidence files into Vault.")
                return redirect(f"{reverse('cases:case_detail', kwargs={'pk': case.pk})}#evidence")

        return redirect('evidence:evidence_upload', case_id=case.pk)


class EvidenceDetailView(LoginRequiredMixin, DetailView):
    """
    Forensic evidence detail view with in-browser previews, SHA-256 verification,
    full version lineage, custody chain, and integrity check audit logs.
    """
    model = Evidence
    template_name = 'evidence/evidence_detail.html'
    context_object_name = 'evidence'

    def get_object(self, queryset: QuerySet | None = None) -> Evidence:
        evidence = super().get_object(queryset)
        if not check_case_access(self.request.user, evidence.case):
            raise PermissionDenied("You do not have access to evidence in this case.")
        return evidence

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        evidence = self.object
        user = self.request.user

        # Chain of Custody
        custody_history = CustodyEvent.objects.filter(
            evidence=evidence
        ).select_related('from_user', 'to_user', 'resolved_by').order_by('-requested_at')
        context['custody_history'] = custody_history

        # Integrity checks
        integrity_checks = evidence.integrity_checks.all().select_related('checked_by').order_by('-checked_on')[:20]
        context['integrity_checks'] = integrity_checks

        # Version lineage (all items with same root parent or children)
        root = evidence
        while root.parent:
            root = root.parent

        def get_all_descendants(item):
            desc = [item]
            for child in item.newer_versions.all().order_by('version'):
                desc.extend(get_all_descendants(child))
            return desc

        all_versions = get_all_descendants(root)
        all_versions.sort(key=lambda x: x.version, reverse=True)
        context['versions'] = all_versions

        # Determine preview capability
        mime = (evidence.mime_type or '').lower()
        ext = os.path.splitext(evidence.original_filename)[1].lower()

        context['is_image'] = ('image/' in mime) or (ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'))
        context['is_pdf'] = ('pdf' in mime) or (ext == '.pdf')
        context['is_audio'] = ('audio/' in mime) or (ext in ('.mp3', '.wav', '.ogg', '.m4a'))
        context['is_video'] = ('video/' in mime) or (ext in ('.mp4', '.webm', '.ogg', '.mov'))
        context['is_text'] = ('text/' in mime) or (ext in ('.txt', '.log', '.csv', '.json', '.xml'))

        context['is_reviewer'] = getattr(user, 'is_reviewer', False)
        is_manager = getattr(user, 'is_admin', False) or getattr(user, 'is_case_manager', False)
        context['can_manage'] = is_manager

        return context


class EvidenceDownloadView(LoginRequiredMixin, View):
    """
    Secure file streaming download directly from outside the web root.
    Verifies user permissions and records immutable download audit trail.
    """

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        evidence = get_object_or_404(Evidence, pk=pk)
        if not check_case_access(request.user, evidence.case):
            raise PermissionDenied("You do not have permission to download this evidence.")

        file_path = get_evidence_file_path(evidence)
        if not file_path.exists() or not file_path.is_file():
            messages.error(request, "Evidence physical file not found on storage disk.")
            raise Http404("Evidence physical file is missing from vault storage.")

        # Log download action
        log_action(
            user=request.user,
            action='evidence.download',
            obj=evidence,
            case=evidence.case,
            request=request,
            details={
                'evidence_no': evidence.evidence_no,
                'sha256': evidence.sha256,
                'file_size': evidence.file_size,
            },
        )

        # Stream file response
        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=evidence.original_filename,
            content_type=evidence.mime_type or 'application/octet-stream',
        )
        return response


class EvidencePreviewView(LoginRequiredMixin, View):
    """
    Streams evidence file content inline (without attachment header)
    for browser display of images, PDFs, audio, and video players.
    """

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        evidence = get_object_or_404(Evidence, pk=pk)
        if not check_case_access(request.user, evidence.case):
            raise PermissionDenied("Access to preview this evidence is denied.")

        file_path = get_evidence_file_path(evidence)
        if not file_path.exists() or not file_path.is_file():
            raise Http404("File not found on vault disk.")

        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=False,
            filename=evidence.original_filename,
            content_type=evidence.mime_type or 'application/octet-stream',
        )
        return response


class EvidenceVerifyView(LoginRequiredMixin, View):
    """
    AJAX endpoint to verify evidence integrity against stored SHA-256 hash.
    Records IntegrityCheck entry and triggers alerts if tampering is detected.
    """

    def post(self, request: HttpRequest, pk: int) -> JsonResponse:
        evidence = get_object_or_404(Evidence, pk=pk)
        if not check_case_access(request.user, evidence.case):
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

        is_valid, computed_hash = verify_evidence_integrity(evidence)
        result_status = IntegrityCheck.Result.VERIFIED if is_valid else IntegrityCheck.Result.MODIFIED

        check = IntegrityCheck.objects.create(
            evidence=evidence,
            checked_by=request.user,
            result=result_status,
            computed_hash=computed_hash or 'FILE_NOT_FOUND',
            stored_hash=evidence.sha256,
            checked_on=timezone.now(),
        )

        if not is_valid:
            evidence.status = Evidence.Status.FLAGGED
            evidence.save(update_fields=['status'])

            # Send alert notification
            create_notification(
                user=request.user,
                message=f"INTEGRITY ALERT: Evidence {evidence.evidence_no} failed integrity check.",
                link=reverse('evidence:evidence_detail', kwargs={'pk': evidence.pk}),
                notification_type=Notification.NotificationType.DANGER,
            )

            log_action(
                user=request.user,
                action='evidence.integrity_failure',
                obj=evidence,
                case=evidence.case,
                request=request,
                details={
                    'computed_hash': computed_hash,
                    'stored_hash': evidence.sha256,
                    'check_id': check.pk,
                },
            )

            return JsonResponse({
                'status': 'modified',
                'is_valid': False,
                'computed_hash': computed_hash,
                'stored_hash': evidence.sha256,
                'result_label': 'TAMPERED / MISMATCH',
                'checked_on': check.checked_on.strftime('%Y-%m-%d %H:%M:%S UTC'),
            })

        log_action(
            user=request.user,
            action='evidence.integrity_verified',
            obj=evidence,
            case=evidence.case,
            request=request,
            details={
                'computed_hash': computed_hash,
                'check_id': check.pk,
            },
        )

        return JsonResponse({
            'status': 'verified',
            'is_valid': True,
            'computed_hash': computed_hash,
            'stored_hash': evidence.sha256,
            'result_label': 'VERIFIED INTACT',
            'checked_on': check.checked_on.strftime('%Y-%m-%d %H:%M:%S UTC'),
        })


class EvidenceBulkVerifyView(LoginRequiredMixin, View):
    """
    Initiate bulk cryptographic verification across all evidence items in a case.
    Dispatches Celery background worker if available; otherwise falls back to synchronous execution.
    """

    def post(self, request: HttpRequest, case_id: int) -> HttpResponse:
        case = get_object_or_404(Case, pk=case_id)
        if not check_case_access(request.user, case):
            raise PermissionDenied("You do not have access to this case.")

        # Try Celery async dispatch
        dispatched_async = False
        try:
            from apps.evidence.tasks import verify_case_evidence_task
            task_result = verify_case_evidence_task.delay(case.pk, request.user.pk)
            dispatched_async = True
        except Exception:
            # Fallback to synchronous verification
            pass

        if dispatched_async:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'queued', 'message': 'Bulk verification dispatched to background worker.'})
            messages.info(request, "Bulk verification task dispatched to background worker.")
            return redirect(f"{reverse('cases:case_detail', kwargs={'pk': case.pk})}#evidence")

        # Synchronous fallback execution
        from apps.evidence.tasks import verify_case_evidence_task
        summary = verify_case_evidence_task(case.pk, request.user.pk)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(summary)

        messages.success(
            request,
            f"Bulk check completed: {summary.get('verified', 0)} of {summary.get('total', 0)} evidence items verified intact."
        )
        return redirect(f"{reverse('cases:case_detail', kwargs={'pk': case.pk})}#evidence")


class EvidenceQRView(LoginRequiredMixin, View):
    """
    Generates and returns forensic QR tracking labels.
    Serves PNG image stream or renders printable layout label.
    """

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        evidence = get_object_or_404(Evidence, pk=pk)
        if not check_case_access(request.user, evidence.case):
            raise PermissionDenied("Access to evidence QR code denied.")

        # If image format requested, return PNG
        if request.GET.get('format') == 'image':
            qr_bytes = generate_qr_label(evidence, request)
            return HttpResponse(qr_bytes, content_type='image/png')

        # Otherwise render printable label page
        return render(
            request,
            'evidence/evidence_qr_label.html',
            {
                'evidence': evidence,
                'case': evidence.case,
                'qr_image_url': f"{reverse('evidence:evidence_qr', kwargs={'pk': evidence.pk})}?format=image",
            },
        )


class EvidenceUpdateView(LoginRequiredMixin, ReadOnlyMixin, UpdateView):
    """
    Modify metadata (title, description, tags) of an existing evidence record.
    Physical file, evidence_no, and SHA-256 remain strictly immutable.
    """
    model = Evidence
    form_class = EvidenceUpdateForm
    template_name = 'evidence/evidence_update.html'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        evidence = self.get_object()
        if not check_case_access(request.user, evidence.case):
            raise PermissionDenied("You do not have access to edit this evidence.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: EvidenceUpdateForm) -> HttpResponse:
        response = super().form_valid(form)
        evidence = self.object

        # Update tags
        tag_names = form.get_tag_names()
        evidence.tags.clear()
        for t_name in tag_names:
            tag_obj, _ = Tag.objects.get_or_create(name=t_name)
            evidence.tags.add(tag_obj)

        log_action(
            user=self.request.user,
            action='evidence.update',
            obj=evidence,
            case=evidence.case,
            request=self.request,
            details={
                'title': evidence.title,
                'tags': tag_names,
            },
        )

        messages.success(self.request, f"Evidence {evidence.evidence_no} metadata updated.")
        return response

    def get_success_url(self) -> str:
        return reverse('evidence:evidence_detail', kwargs={'pk': self.object.pk})
