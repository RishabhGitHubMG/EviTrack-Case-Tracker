from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.mixins import get_user_accessible_cases
from apps.cases.models import Case
from apps.custody.models import CustodyEvent
from apps.evidence.models import Evidence

OPEN_CASE_STATUSES = [Case.Status.OPEN, Case.Status.UNDER_INVESTIGATION, Case.Status.IN_COURT]


def _visible_evidence(user: Any):
    return Evidence.objects.filter(case__in=get_user_accessible_cases(user), is_latest_version=True)


class LandingView(TemplateView):
    template_name = 'landing.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cases = get_user_accessible_cases(user)
        evidence = _visible_evidence(user)
        pending_custody = CustodyEvent.objects.filter(
            evidence__in=evidence, status=CustodyEvent.Status.REQUESTED
        )
        context.update({
            'total_cases': cases.count(),
            'open_cases': cases.filter(status__in=OPEN_CASE_STATUSES).count(),
            'evidence_count': evidence.count(),
            'flagged_evidence': evidence.filter(status=Evidence.Status.FLAGGED).count(),
            'pending_custody': pending_custody.count(),
            'pending_approvals': self._pending_approvals(user),
            'recent_cases': cases.select_related('created_by').order_by('-opened_on', '-id')[:5],
            'charts_url': reverse('core:dashboard_charts'),
        })
        return context

    def _pending_approvals(self, user: Any) -> int | None:
        if not user.is_admin:
            return None
        from apps.accounts.models import User
        return User.objects.filter(is_approved=False, is_active=True).count()


class SearchAPIView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({'results': []})


class DashboardChartsAPIView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        cases = get_user_accessible_cases(request.user)
        evidence = _visible_evidence(request.user)
        case_counts = dict(cases.values_list('status').annotate(n=Count('id')).values_list('status', 'n'))
        evidence_counts = dict(evidence.values_list('status').annotate(n=Count('id')).values_list('status', 'n'))
        return JsonResponse({
            'cases_by_status': {
                'labels': [label for _, label in Case.Status.choices],
                'values': [case_counts.get(value, 0) for value, _ in Case.Status.choices],
            },
            'evidence_by_status': {
                'labels': [label for _, label in Evidence.Status.choices],
                'values': [evidence_counts.get(value, 0) for value, _ in Evidence.Status.choices],
            },
        })


def error_403(request: HttpRequest, exception: Exception = None) -> HttpResponse:
    """Custom 403 Forbidden error handler."""
    return render(request, 'errors/403.html', status=403)


def error_404(request: HttpRequest, exception: Exception = None) -> HttpResponse:
    """Custom 404 Not Found error handler."""
    return render(request, 'errors/404.html', status=404)


def error_500(request: HttpRequest) -> HttpResponse:
    """Custom 500 Internal Server Error handler."""
    return render(request, 'errors/500.html', status=500)
