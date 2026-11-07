"""
Views for the Custody app.
"""
import io
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

import qrcode
from PIL import Image, ImageDraw, ImageFont

from apps.accounts.mixins import CaseAccessMixin, check_case_access, get_user_accessible_cases
from apps.custody.forms import CustodyResponseForm, CustodyTransferForm
from apps.custody.models import CustodyEvent
from apps.custody.services import (
    accept_transfer,
    get_custody_timeline,
    get_pending_transfers_for_user,
    reject_transfer,
    request_transfer,
)
from apps.evidence.models import Evidence


def _get_client_ip(request: HttpRequest) -> str | None:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class CustodyListView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view for Custody transfers and chain-of-custody audit logs.
    Shows incoming pending transfers for the user and recent custody activities.
    """
    template_name = 'custody/custody_list.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user

        pending_transfers = get_pending_transfers_for_user(user)
        accessible_cases = get_user_accessible_cases(user)

        recent_events = (
            CustodyEvent.objects.filter(evidence__case__in=accessible_cases)
            .select_related('evidence', 'evidence__case', 'from_user', 'to_user', 'resolved_by')
            .order_by('-requested_at')[:30]
        )

        context.update({
            'pending_transfers': pending_transfers,
            'recent_events': recent_events,
            'pending_count': pending_transfers.count(),
        })
        return context


class CustodyRequestView(CaseAccessMixin, View):
    """
    View to initiate a custody transfer request for a specific evidence item.
    """
    template_name = 'custody/custody_request.html'

    def get_evidence(self) -> Evidence:
        evidence_id = self.kwargs.get('evidence_id')
        evidence = get_object_or_404(
            Evidence.objects.select_related('case', 'current_holder', 'uploaded_by'),
            pk=evidence_id
        )
        if not check_case_access(self.request.user, evidence.case):
            raise PermissionDenied("You do not have access to this evidence's case.")
        return evidence

    def get(self, request: HttpRequest, evidence_id: int) -> HttpResponse:
        evidence = self.get_evidence()
        form = CustodyTransferForm(evidence=evidence)
        return render(request, self.template_name, {
            'evidence': evidence,
            'form': form,
            'case': evidence.case,
        })

    def post(self, request: HttpRequest, evidence_id: int) -> HttpResponse:
        evidence = self.get_evidence()
        form = CustodyTransferForm(request.POST, evidence=evidence)

        if form.is_valid():
            to_user = form.cleaned_data['to_user']
            reason = form.cleaned_data['reason']
            ip_addr = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            request_transfer(
                evidence=evidence,
                from_user=request.user,
                to_user=to_user,
                reason=reason,
                ip_address=ip_addr,
                user_agent=user_agent,
            )

            messages.success(
                request,
                f"Transfer request for evidence {evidence.evidence_no} submitted to {to_user.get_full_name() or to_user.email}."
            )
            return redirect('custody:custody_list')

        return render(request, self.template_name, {
            'evidence': evidence,
            'form': form,
            'case': evidence.case,
        })


class CustodyRespondView(LoginRequiredMixin, View):
    """
    View to accept or reject an incoming custody transfer.
    Restricted to the designated recipient (to_user) or an Admin.
    """
    template_name = 'custody/custody_respond.html'

    def get_event(self) -> CustodyEvent:
        pk = self.kwargs.get('pk')
        event = get_object_or_404(
            CustodyEvent.objects.select_related(
                'evidence', 'evidence__case', 'from_user', 'to_user'
            ),
            pk=pk
        )
        user = self.request.user

        # Recipient or Admin only
        if event.to_user_id != user.id and not (user.is_superuser or user.is_admin):
            raise PermissionDenied("You are not authorized to respond to this transfer request.")

        return event

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        event = self.get_event()

        if event.status != CustodyEvent.Status.REQUESTED:
            messages.info(request, "This custody transfer request has already been resolved.")
            return redirect('custody:custody_list')

        form = CustodyResponseForm()
        return render(request, self.template_name, {
            'event': event,
            'evidence': event.evidence,
            'case': event.evidence.case,
            'form': form,
        })

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        event = self.get_event()

        if event.status != CustodyEvent.Status.REQUESTED:
            messages.warning(request, "This custody transfer request has already been resolved.")
            return redirect('custody:custody_list')

        form = CustodyResponseForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            reason = form.cleaned_data.get('reason', '').strip()
            ip_addr = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            if action == 'accept':
                accept_transfer(
                    custody_event=event,
                    user=request.user,
                    ip_address=ip_addr,
                    user_agent=user_agent,
                )
                messages.success(
                    request,
                    f"You have accepted custody of evidence {event.evidence.evidence_no}."
                )
            elif action == 'reject':
                reject_transfer(
                    custody_event=event,
                    user=request.user,
                    reason=reason,
                    ip_address=ip_addr,
                    user_agent=user_agent,
                )
                messages.warning(
                    request,
                    f"You have rejected the custody transfer request for {event.evidence.evidence_no}."
                )

            return redirect('custody:custody_list')

        return render(request, self.template_name, {
            'event': event,
            'evidence': event.evidence,
            'case': event.evidence.case,
            'form': form,
        })


class CustodyTimelineView(CaseAccessMixin, View):
    """
    AJAX view returning custody timeline HTML partial for an evidence item.
    """
    template_name = 'custody/custody_timeline.html'

    def get(self, request: HttpRequest, evidence_id: int) -> HttpResponse:
        evidence = get_object_or_404(
            Evidence.objects.select_related('case', 'current_holder', 'uploaded_by'),
            pk=evidence_id
        )
        if not check_case_access(request.user, evidence.case):
            raise PermissionDenied("You do not have access to this evidence's case.")

        timeline = get_custody_timeline(evidence)
        return render(request, self.template_name, {
            'evidence': evidence,
            'timeline': timeline,
        })


class CustodyQRLabelView(CaseAccessMixin, View):
    """
    Generates a printable tamper-evident forensic QR label (PDF or PNG)
    for an evidence item containing evidence_no, case_no, hash prefix, and QR link.
    """

    def get(self, request: HttpRequest, evidence_id: int) -> HttpResponse:
        evidence = get_object_or_404(
            Evidence.objects.select_related('case', 'current_holder', 'uploaded_by'),
            pk=evidence_id
        )
        if not check_case_access(request.user, evidence.case):
            raise PermissionDenied("You do not have access to this evidence's case.")

        # Target URL for QR code
        try:
            target_path = reverse('evidence:evidence_detail', kwargs={'pk': evidence.pk})
        except Exception:
            target_path = f"/evidence/{evidence.pk}/"

        evidence_url = request.build_absolute_uri(target_path)

        # Build QR Code Image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=5,
            border=2,
        )
        qr.add_data(evidence_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#14213D", back_color="#FFFFFF").convert('RGB')

        # Create Label Canvas (600x260 px)
        width, height = 620, 260
        label_img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(label_img)

        # Outer border and banner line
        draw.rectangle([(2, 2), (width - 3, height - 3)], outline='#14213D', width=3)
        draw.rectangle([(4, 4), (width - 5, 42)], fill='#14213D')

        # Header Title
        draw.text((15, 12), "EVITRACK DIGITAL EVIDENCE VAULT", fill='#FFFFFF')
        draw.text((450, 12), "CHAIN OF CUSTODY", fill='#F2A900')

        # Paste QR code
        qr_size = 190
        qr_resized = qr_img.resize((qr_size, qr_size))
        label_img.paste(qr_resized, (20, 52))

        # Information details beside QR
        text_x = 225
        y = 56
        draw.text((text_x, y), f"EVIDENCE NO: {evidence.evidence_no}", fill='#14213D')
        y += 24
        draw.text((text_x, y), f"CASE NO:     {evidence.case.case_no}", fill='#14213D')
        y += 24
        title_snippet = evidence.title[:35] + ("..." if len(evidence.title) > 35 else "")
        draw.text((text_x, y), f"TITLE:       {title_snippet}", fill='#2D3748')
        y += 24
        holder_name = (
            evidence.current_holder.get_full_name() or evidence.current_holder.email
            if evidence.current_holder else "Vault Intake"
        )
        draw.text((text_x, y), f"CUSTODIAN:   {holder_name}", fill='#2D3748')
        y += 24
        hash_short = f"{evidence.sha256[:16]}...{evidence.sha256[-8:]}" if evidence.sha256 else "N/A"
        draw.text((text_x, y), f"SHA-256:     {hash_short}", fill='#059669')
        y += 24
        draw.text((text_x, y), f"INTAKE DATE: {evidence.uploaded_at:%Y-%m-%d %H:%M UTC}", fill='#718096')
        y += 24
        draw.text((text_x, y), f"SEC LEVEL:   CJIS / ISO 27037 FORENSIC SEAL", fill='#DC2626')

        requested_format = request.GET.get('format', 'png').lower()
        buf = io.BytesIO()

        if requested_format == 'pdf':
            label_img.save(buf, format='PDF', resolution=150.0)
            content_type = 'application/pdf'
            filename = f"label_{evidence.evidence_no}.pdf"
        else:
            label_img.save(buf, format='PNG')
            content_type = 'image/png'
            filename = f"label_{evidence.evidence_no}.png"

        buf.seek(0)
        response = HttpResponse(buf.getvalue(), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
