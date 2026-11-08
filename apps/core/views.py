from collections.abc import Iterable
from datetime import date, datetime, timedelta
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.mixins import get_user_accessible_cases
from apps.cases.models import Case, Party
from apps.custody.models import CustodyEvent
from apps.evidence.models import Evidence
from apps.hearings.models import Hearing, Task

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


SEARCH_CATEGORIES = ('Cases', 'Parties', 'Evidence')


def _grouped_search(user: Any, query: str, limit: int) -> list[dict[str, str]]:
    accessible_cases = get_user_accessible_cases(user)
    results = []
    cases = Case.objects.filter(pk__in=accessible_cases).filter(
        Q(case_no__icontains=query) | Q(title__icontains=query)
    ).order_by('case_no')[:limit]
    results.extend({
        'category': 'Cases',
        'title': f'{case.case_no} — {case.title}',
        'subtitle': case.get_status_display(),
        'url': reverse('cases:case_detail', kwargs={'pk': case.pk}),
        'icon': 'bi-folder2-open',
    } for case in cases)

    parties = Party.objects.filter(case__in=accessible_cases).filter(
        Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query)
    ).select_related('case').order_by('name').distinct()[:limit]
    results.extend({
        'category': 'Parties',
        'title': party.name,
        'subtitle': f'{party.get_party_type_display()} · {party.case.case_no}',
        'url': f"{reverse('cases:case_detail', kwargs={'pk': party.case_id})}#parties",
        'icon': 'bi-person-vcard',
    } for party in parties)

    evidence_items = Evidence.objects.filter(case__in=accessible_cases, is_latest_version=True).filter(
        Q(evidence_no__icontains=query)
        | Q(title__icontains=query)
        | Q(sha256__icontains=query)
        | Q(tags__name__icontains=query)
    ).select_related('case').order_by('evidence_no').distinct()[:limit]
    results.extend({
        'category': 'Evidence',
        'title': f'{item.evidence_no} — {item.title}',
        'subtitle': f'{item.case.case_no} · {item.get_status_display()}',
        'url': reverse('evidence:evidence_detail', kwargs={'pk': item.pk}),
        'icon': 'bi-file-earmark-lock',
    } for item in evidence_items)
    return results


def _clean_query(request: HttpRequest) -> str:
    return request.GET.get('q', '').strip()[:100]


class SearchAPIView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        query = _clean_query(request)
        if len(query) < 2:
            return JsonResponse({'results': []})
        return JsonResponse({'results': _grouped_search(request.user, query, limit=5)})


class SearchPageView(LoginRequiredMixin, TemplateView):
    template_name = 'core/search.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        query = _clean_query(self.request)
        groups = []
        if len(query) >= 2:
            results = _grouped_search(self.request.user, query, limit=25)
            for category in SEARCH_CATEGORIES:
                items = [item for item in results if item['category'] == category]
                if items:
                    groups.append({'name': category, 'items': items})
        context.update({
            'query': query,
            'groups': groups,
            'total_results': sum(len(group['items']) for group in groups),
            'searched': len(query) >= 2,
        })
        return context


CHART_WEEKS = 8


def _week_starts(future: bool) -> list[date]:
    today = timezone.localdate()
    this_monday = today - timedelta(days=today.weekday())
    if future:
        return [this_monday + timedelta(weeks=offset) for offset in range(CHART_WEEKS)]
    return [this_monday - timedelta(weeks=offset) for offset in reversed(range(CHART_WEEKS))]


def _week_label(monday: date) -> str:
    return monday.strftime('%d %b')


def _count_by_week(moments: Iterable[datetime], starts: list[date]) -> list[int]:
    index = {start: position for position, start in enumerate(starts)}
    counts = [0] * len(starts)
    for moment in moments:
        day = timezone.localdate(moment)
        monday = day - timedelta(days=day.weekday())
        if monday in index:
            counts[index[monday]] += 1
    return counts


class DashboardChartsAPIView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        cases = get_user_accessible_cases(request.user)
        evidence = _visible_evidence(request.user)
        case_counts = dict(cases.values_list('status').annotate(n=Count('id')).values_list('status', 'n'))
        evidence_counts = dict(evidence.values_list('status').annotate(n=Count('id')).values_list('status', 'n'))
        type_counts = dict(cases.values_list('case_type').annotate(n=Count('id')).values_list('case_type', 'n'))

        upcoming = _week_starts(future=True)
        hearing_moments = Hearing.objects.filter(
            case__in=cases,
            hearing_date__date__gte=upcoming[0],
            hearing_date__date__lt=upcoming[-1] + timedelta(days=7),
        ).values_list('hearing_date', flat=True)

        past = _week_starts(future=False)
        upload_moments = Evidence.objects.filter(
            case__in=cases, uploaded_at__date__gte=past[0]
        ).values_list('uploaded_at', flat=True)

        workload_rows = (
            Task.objects.filter(case__in=cases)
            .exclude(status=Task.Status.COMPLETED)
            .values('assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__email')
            .annotate(n=Count('id'))
            .order_by('-n', 'assigned_to__email')[:8]
        )

        return JsonResponse({
            'cases_by_status': {
                'labels': [label for _, label in Case.Status.choices],
                'values': [case_counts.get(value, 0) for value, _ in Case.Status.choices],
            },
            'evidence_by_status': {
                'labels': [label for _, label in Evidence.Status.choices],
                'values': [evidence_counts.get(value, 0) for value, _ in Evidence.Status.choices],
            },
            'cases_by_type': {
                'labels': [label for _, label in Case.CaseType.choices],
                'values': [type_counts.get(value, 0) for value, _ in Case.CaseType.choices],
            },
            'hearings_per_week': {
                'labels': [_week_label(start) for start in upcoming],
                'values': _count_by_week(hearing_moments, upcoming),
            },
            'evidence_uploads': {
                'labels': [_week_label(start) for start in past],
                'values': _count_by_week(upload_moments, past),
            },
            'workload_per_user': {
                'labels': [
                    f"{row['assigned_to__first_name']} {row['assigned_to__last_name']}".strip()
                    or row['assigned_to__email']
                    for row in workload_rows
                ],
                'values': [row['n'] for row in workload_rows],
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
