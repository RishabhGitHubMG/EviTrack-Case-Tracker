import csv
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.views.generic import ListView, View

from apps.accounts.mixins import AdminRequiredMixin, get_user_accessible_cases
from apps.audit.models import AuditLog


def filtered_audit_logs(request, user=None):
    accessible_cases = get_user_accessible_cases(request.user)
    queryset = AuditLog.objects.select_related('user', 'case')
    if user is not None:
        queryset = queryset.filter(user=user).filter(
            Q(case__in=accessible_cases) | Q(case__isnull=True)
        )
    elif not (request.user.is_admin or request.user.is_superuser):
        queryset = queryset.filter(
            Q(case__in=accessible_cases) | Q(case__isnull=True, user=request.user)
        )

    action = request.GET.get('action', '').strip()[:100]
    if action:
        queryset = queryset.filter(action__icontains=action)

    user_id = request.GET.get('user', '').strip()
    if user_id.isdigit():
        queryset = queryset.filter(user_id=int(user_id))

    case_id = request.GET.get('case', '').strip()
    if case_id.isdigit():
        queryset = queryset.filter(case_id=int(case_id))

    date_from = parse_date(request.GET.get('date_from', ''))
    if date_from:
        queryset = queryset.filter(timestamp__date__gte=date_from)

    date_to = parse_date(request.GET.get('date_to', ''))
    if date_to:
        queryset = queryset.filter(timestamp__date__lte=date_to)

    return queryset.order_by('-timestamp', '-pk')


def export_audit_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit-log.csv"'
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'User', 'Action', 'Case', 'Object ID', 'IP Address', 'Details'])
    for entry in queryset.iterator():
        writer.writerow([
            entry.timestamp.isoformat(),
            entry.user.email if entry.user else 'System',
            entry.action,
            entry.case.case_no if entry.case else '',
            entry.object_id,
            entry.ip_address or '',
            json.dumps(entry.details, sort_keys=True),
        ])
    return response


class AuditLogListView(AdminRequiredMixin, ListView):
    model = AuditLog
    template_name = 'audit/audit_log_list.html'
    context_object_name = 'audit_entries'
    paginate_by = 50

    def get_queryset(self):
        return filtered_audit_logs(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = AuditLog.objects.filter(user__isnull=False).values_list(
            'user_id', 'user__email'
        ).distinct().order_by('user__email')
        context['cases'] = get_user_accessible_cases(self.request.user).order_by('case_no')
        return context


class AuditLogExportView(AdminRequiredMixin, View):
    def get(self, request):
        return export_audit_csv(filtered_audit_logs(request))


class MyActivityView(LoginRequiredMixin, ListView):
    template_name = 'audit/audit_log_list.html'
    context_object_name = 'audit_entries'
    paginate_by = 50

    def get_queryset(self):
        return filtered_audit_logs(self.request, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_activity'] = True
        return context
