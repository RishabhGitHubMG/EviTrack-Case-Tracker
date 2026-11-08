from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from weasyprint import HTML

from apps.accounts.mixins import get_user_accessible_cases
from apps.audit.services import log_action
from apps.cases.models import Case, Party
from apps.custody.models import CustodyEvent


def _case_summary(case):
    evidence = case.evidence_items.order_by('evidence_no')
    hearings = case.hearings.order_by('hearing_date')
    tasks = case.tasks.order_by('due_date')
    parties = Party.objects.filter(case=case).order_by('name')
    return [
        {'heading': 'Case', 'rows': [
            ['Case number', case.case_no], ['Title', case.title],
            ['Type', case.get_case_type_display()], ['Status', case.get_status_display()],
            ['Priority', case.get_priority_display()], ['Opened', case.opened_on.strftime('%Y-%m-%d')],
            ['Description', case.description],
        ]},
        {'heading': 'Parties', 'columns': ['Name', 'Type', 'Email', 'Phone'], 'rows': [
            [party.name, party.get_party_type_display(), party.email, party.phone] for party in parties
        ]},
        {'heading': 'Evidence', 'columns': ['Number', 'Title', 'Status', 'Uploaded'], 'rows': [
            [item.evidence_no, item.title, item.get_status_display(), item.uploaded_at.strftime('%Y-%m-%d %H:%M UTC')]
            for item in evidence
        ]},
        {'heading': 'Hearings', 'columns': ['Date', 'Court', 'Purpose'], 'rows': [
            [hearing.hearing_date.strftime('%Y-%m-%d %H:%M UTC'), hearing.court, hearing.purpose]
            for hearing in hearings
        ]},
        {'heading': 'Tasks', 'columns': ['Title', 'Assignee', 'Due', 'Status'], 'rows': [
            [task.title, task.assigned_to.email, task.due_date.strftime('%Y-%m-%d %H:%M UTC'), task.get_status_display()]
            for task in tasks
        ]},
    ]


def _evidence_register(case):
    evidence = case.evidence_items.select_related('uploaded_by', 'current_holder').order_by('evidence_no')
    return [{'heading': 'Evidence Register', 'columns': [
        'Evidence No.', 'Title', 'Filename', 'SHA-256', 'Size (bytes)', 'Status', 'Uploaded by', 'Uploaded at'
    ], 'rows': [
        [item.evidence_no, item.title, item.original_filename, item.sha256, str(item.file_size),
         item.get_status_display(), item.uploaded_by.email, item.uploaded_at.strftime('%Y-%m-%d %H:%M UTC')]
        for item in evidence
    ]}]


def _custody_history(case):
    events = CustodyEvent.objects.filter(evidence__case=case).select_related(
        'evidence', 'from_user', 'to_user', 'resolved_by'
    ).order_by('requested_at', 'pk')
    return [{'heading': 'Custody History', 'columns': [
        'Evidence', 'From', 'To', 'Status', 'Reason', 'Requested', 'Resolved', 'Resolved by'
    ], 'rows': [
        [event.evidence.evidence_no,
         event.from_user.email if event.from_user else 'Initial intake',
         event.to_user.email, event.get_status_display(), event.reason,
         event.requested_at.strftime('%Y-%m-%d %H:%M UTC'),
         event.resolved_at.strftime('%Y-%m-%d %H:%M UTC') if event.resolved_at else '',
         event.resolved_by.email if event.resolved_by else '']
        for event in events
    ]}]


def _hearing_schedule(case):
    hearings = case.hearings.order_by('hearing_date')
    return [{'heading': 'Hearing Schedule', 'columns': [
        'Date', 'Court', 'Purpose', 'Outcome', 'Next hearing'
    ], 'rows': [
        [hearing.hearing_date.strftime('%Y-%m-%d %H:%M UTC'), hearing.court, hearing.purpose,
         hearing.outcome, hearing.next_hearing_date.strftime('%Y-%m-%d %H:%M UTC') if hearing.next_hearing_date else '']
        for hearing in hearings
    ]}]


def _integrity_report(case):
    evidence_items = case.evidence_items.prefetch_related('integrity_checks').order_by('evidence_no')
    rows = []
    for item in evidence_items:
        checks = list(item.integrity_checks.order_by('-checked_on'))
        if checks:
            for check in reversed(checks):
                rows.append([
                    item.evidence_no, item.title, check.get_result_display(), item.sha256,
                    check.computed_hash, check.checked_by.email, check.checked_on.strftime('%Y-%m-%d %H:%M UTC'),
                ])
        else:
            rows.append([item.evidence_no, item.title, 'Not checked', item.sha256, '', '', ''])
    return [{'heading': 'Integrity Report', 'columns': [
        'Evidence No.', 'Title', 'Result', 'Stored SHA-256', 'Computed SHA-256', 'Checked by', 'Checked at'
    ], 'rows': rows}]


REPORTS = {
    'case_summary': ('Case Summary', _case_summary),
    'evidence_register': ('Evidence Register', _evidence_register),
    'custody_history': ('Chain of Custody History', _custody_history),
    'hearing_schedule': ('Hearing Schedule', _hearing_schedule),
    'integrity_report': ('Integrity Report', _integrity_report),
}


class ReportListView(LoginRequiredMixin, View):
    def get(self, request):
        accessible_cases = get_user_accessible_cases(request.user).order_by('case_no')
        cases = accessible_cases
        selected_case = request.GET.get('case', '').strip()
        if selected_case.isdigit():
            selected_case = int(selected_case)
            cases = cases.filter(pk=selected_case)
        else:
            selected_case = ''
        return render(request, 'reports/report_list.html', {
            'cases': cases,
            'accessible_cases': accessible_cases,
            'selected_case': selected_case,
        })


class CaseReportView(LoginRequiredMixin, View):
    report_type = None

    def get(self, request, case_id):
        case = get_object_or_404(get_user_accessible_cases(request.user), pk=case_id)
        title, builder = REPORTS[self.report_type]
        document = render_to_string('reports/report_pdf.html', {
            'title': title,
            'case': case,
            'generated_by': request.user.get_full_name() or request.user.email,
            'generated_at': timezone.localtime(timezone.now()),
            'sections': builder(case),
        })
        pdf = HTML(string=document, base_url=request.build_absolute_uri('/')).write_pdf()
        log_action(
            user=request.user,
            action=f'report.{self.report_type}.generated',
            obj=case,
            case=case,
            request=request,
        )
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{case.case_no}-{self.report_type}.pdf"'
        return response


class CaseSummaryReportView(CaseReportView):
    report_type = 'case_summary'


class EvidenceRegisterReportView(CaseReportView):
    report_type = 'evidence_register'


class CustodyHistoryReportView(CaseReportView):
    report_type = 'custody_history'


class HearingScheduleReportView(CaseReportView):
    report_type = 'hearing_schedule'


class IntegrityReportView(CaseReportView):
    report_type = 'integrity_report'
