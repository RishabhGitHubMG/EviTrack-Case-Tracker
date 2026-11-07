"""
Views for the Cases app: Case listing, creation, updates, detail, assignments, parties, and timeline.
"""
from typing import Any
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.mixins import (
    AdminRequiredMixin,
    CaseAccessMixin,
    CaseManagerOrAdminMixin,
    ReadOnlyMixin,
    get_user_accessible_cases,
    require_case_access,
)
from apps.audit.models import AuditLog
from apps.audit.services import log_action
from apps.cases.forms import (
    CaseAssignmentForm,
    CaseCreateForm,
    CaseFilterForm,
    CaseUpdateForm,
    PartyForm,
)
from apps.cases.models import Case, CaseAssignment, Party
from apps.custody.models import CustodyEvent
from apps.evidence.models import Evidence
from apps.hearings.models import Hearing, Task

User = get_user_model()


class CaseListView(LoginRequiredMixin, CaseAccessMixin, ListView):
    """
    Paginated, filterable, sortable list of cases accessible to the authenticated user.
    """
    model = Case
    template_name = 'cases/case_list.html'
    context_object_name = 'cases'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        qs = get_user_accessible_cases(self.request.user)
        qs = qs.select_related('created_by').prefetch_related('assignments__user')

        # Apply search and filters from GET parameters
        form = CaseFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                qs = qs.filter(
                    Q(case_no__icontains=q) |
                    Q(title__icontains=q) |
                    Q(description__icontains=q)
                )

            status = form.cleaned_data.get('status')
            if status:
                qs = qs.filter(status=status)

            priority = form.cleaned_data.get('priority')
            if priority:
                qs = qs.filter(priority=priority)

            case_type = form.cleaned_data.get('case_type')
            if case_type:
                qs = qs.filter(case_type=case_type)

        # Dynamic Sorting
        sort_by = self.request.GET.get('sort', '-opened_on')
        direction = self.request.GET.get('dir', 'desc')
        allowed_sorts = {
            'case_no': 'case_no',
            'title': 'title',
            'case_type': 'case_type',
            'status': 'status',
            'priority': 'priority',
            'opened_on': 'opened_on',
        }

        order_field = allowed_sorts.get(sort_by.lstrip('-'), 'opened_on')
        if direction == 'asc' or (not sort_by.startswith('-') and direction != 'desc'):
            qs = qs.order_by(order_field, '-id')
        else:
            qs = qs.order_by(f"-{order_field}", '-id')

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user_cases = get_user_accessible_cases(self.request.user)
        context['filter_form'] = CaseFilterForm(self.request.GET)
        context['total_cases_count'] = user_cases.count()
        context['open_cases_count'] = user_cases.filter(status=Case.Status.OPEN).count()
        context['active_cases_count'] = user_cases.filter(
            status__in=[Case.Status.OPEN, Case.Status.UNDER_INVESTIGATION, Case.Status.IN_COURT]
        ).count()
        context['current_sort'] = self.request.GET.get('sort', 'opened_on')
        context['current_dir'] = self.request.GET.get('dir', 'desc')
        return context


class CaseCreateView(LoginRequiredMixin, ReadOnlyMixin, CreateView):
    """
    Create a new case. Automatically assigns creator as Lead on the case and records audit trail.
    """
    model = Case
    form_class = CaseCreateForm
    template_name = 'cases/case_create.html'

    def form_valid(self, form: CaseCreateForm) -> HttpResponse:
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        case = self.object

        # Auto-assign creator as Lead
        CaseAssignment.objects.get_or_create(
            case=case,
            user=self.request.user,
            defaults={'role_on_case': CaseAssignment.RoleOnCase.LEAD},
        )

        # Audit Log
        log_action(
            user=self.request.user,
            action='case.create',
            obj=case,
            case=case,
            request=self.request,
            details={
                'case_no': case.case_no,
                'title': case.title,
                'case_type': case.case_type,
                'priority': case.priority,
            },
        )

        messages.success(self.request, f"Case {case.case_no} created successfully.")
        return response

    def get_success_url(self) -> str:
        return reverse('cases:case_detail', kwargs={'pk': self.object.pk})


class CaseUpdateView(LoginRequiredMixin, ReadOnlyMixin, CaseAccessMixin, UpdateView):
    """
    Edit case details with strict status transition enforcement and audit logging.
    """
    model = Case
    form_class = CaseUpdateForm
    template_name = 'cases/case_update.html'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        case = self.get_object()
        user = request.user
        # Only Admin, Case Manager, or designated Lead can edit core case properties
        is_lead = case.assignments.filter(user=user, role_on_case=CaseAssignment.RoleOnCase.LEAD).exists()
        can_edit = getattr(user, 'is_admin', False) or getattr(user, 'is_case_manager', False) or is_lead
        if not can_edit:
            raise PermissionDenied("Only Case Managers, Admins, or Case Leads can modify case details.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: CaseUpdateForm) -> HttpResponse:
        old_status = self.object.status
        response = super().form_valid(form)
        case = self.object

        # Audit Log
        log_action(
            user=self.request.user,
            action='case.update',
            obj=case,
            case=case,
            request=self.request,
            details={
                'case_no': case.case_no,
                'status_previous': old_status,
                'status_new': case.status,
                'priority': case.priority,
                'closed_on': str(case.closed_on) if case.closed_on else None,
            },
        )

        messages.success(self.request, f"Case {case.case_no} updated successfully.")
        return response

    def get_success_url(self) -> str:
        return reverse('cases:case_detail', kwargs={'pk': self.object.pk})


class CaseDetailView(LoginRequiredMixin, CaseAccessMixin, DetailView):
    """
    Comprehensive tabbed detail view for a case:
    Overview, Parties, Evidence, Custody, Hearings, Tasks, Timeline, and Audit logs.
    """
    model = Case
    template_name = 'cases/case_detail.html'
    context_object_name = 'case'

    def get_queryset(self) -> QuerySet:
        return Case.objects.all().select_related('created_by').prefetch_related(
            'assignments__user',
            'parties',
            'evidence_items__tags',
            'evidence_items__uploaded_by',
            'evidence_items__current_holder',
            'hearings__created_by',
            'tasks__assigned_to',
            'tasks__created_by',
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        case = self.object
        user = self.request.user

        # Assignments
        assignments = case.assignments.all().select_related('user')
        context['assignments'] = assignments

        # Parties
        parties = case.parties.all()
        context['parties'] = parties

        # Evidence Items (latest versions primary)
        evidence_items = case.evidence_items.all().select_related(
            'uploaded_by', 'current_holder'
        ).prefetch_related('tags')
        context['evidence_items'] = evidence_items

        # Custody Events for this case's evidence
        custody_events = CustodyEvent.objects.filter(
            evidence__case=case
        ).select_related('evidence', 'from_user', 'to_user', 'resolved_by').order_by('-requested_at')
        context['custody_events'] = custody_events

        # Hearings
        hearings = case.hearings.all().select_related('created_by').order_by('hearing_date')
        context['hearings'] = hearings

        # Tasks
        tasks = case.tasks.all().select_related('assigned_to', 'created_by').order_by('due_date')
        context['tasks'] = tasks

        # Audit logs for this case
        audit_entries = AuditLog.objects.filter(case=case).select_related('user').order_by('-timestamp')[:50]
        context['audit_entries'] = audit_entries

        # Permission checks
        is_manager_or_admin = getattr(user, 'is_admin', False) or getattr(user, 'is_case_manager', False)
        is_lead = assignments.filter(user=user, role_on_case=CaseAssignment.RoleOnCase.LEAD).exists()
        context['can_manage'] = is_manager_or_admin or is_lead
        context['is_reviewer'] = getattr(user, 'is_reviewer', False)

        # Inline/Modal Forms
        context['assignment_form'] = CaseAssignmentForm()
        context['party_form'] = PartyForm()

        # Tab navigation active state
        context['active_tab'] = self.request.GET.get('tab', 'overview')

        # Quick stats
        context['stats'] = {
            'evidence_count': evidence_items.count(),
            'hearings_count': hearings.count(),
            'tasks_count': tasks.count(),
            'parties_count': parties.count(),
            'custody_count': custody_events.count(),
        }

        return context


class CaseAssignView(LoginRequiredMixin, CaseManagerOrAdminMixin, ReadOnlyMixin, CaseAccessMixin, View):
    """
    Assign an approved user to a case with a designated role (Lead, Member, Observer).
    """

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        case = get_object_or_404(Case, pk=pk)
        require_case_access(self.request.user, case)

        form = CaseAssignmentForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            role_on_case = form.cleaned_data['role_on_case']

            assignment, created = CaseAssignment.objects.update_or_create(
                case=case,
                user=user,
                defaults={'role_on_case': role_on_case},
            )

            action_name = 'case.assignment.add' if created else 'case.assignment.update'
            log_action(
                user=request.user,
                action=action_name,
                obj=assignment,
                case=case,
                request=request,
                details={
                    'assigned_user_id': user.pk,
                    'assigned_user_email': user.email,
                    'role_on_case': role_on_case,
                },
            )

            role_label = assignment.get_role_on_case_display()
            messages.success(request, f"{user} has been assigned as {role_label}.")
        else:
            for field, errs in form.errors.items():
                messages.error(request, f"Assignment Error ({field}): {errs.as_text()}")

        return redirect(f"{reverse('cases:case_detail', kwargs={'pk': pk})}#overview")


class CaseUnassignView(LoginRequiredMixin, CaseManagerOrAdminMixin, ReadOnlyMixin, CaseAccessMixin, View):
    """
    Remove an assigned user from a case.
    """

    def post(self, request: HttpRequest, pk: int, assignment_id: int) -> HttpResponse:
        case = get_object_or_404(Case, pk=pk)
        require_case_access(self.request.user, case)

        assignment = get_object_or_404(CaseAssignment, pk=assignment_id, case=case)
        assigned_user = assignment.user
        role_label = assignment.get_role_on_case_display()

        assignment.delete()

        log_action(
            user=request.user,
            action='case.assignment.remove',
            obj=case,
            case=case,
            request=request,
            details={
                'removed_user_id': assigned_user.pk,
                'removed_user_email': assigned_user.email,
                'role_on_case': role_label,
            },
        )

        messages.success(request, f"Removed {assigned_user} from case assignments.")
        return redirect(f"{reverse('cases:case_detail', kwargs={'pk': pk})}#overview")


class PartyCreateView(LoginRequiredMixin, ReadOnlyMixin, CaseAccessMixin, View):
    """
    Add a new party (complainant, accused, witness, client, opposing counsel) to a case.
    """

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        case = get_object_or_404(Case, pk=pk)
        require_case_access(self.request.user, case)

        form = PartyForm(request.POST)
        if form.is_valid():
            party = form.save(commit=False)
            party.case = case
            party.save()

            log_action(
                user=request.user,
                action='case.party.add',
                obj=party,
                case=case,
                request=request,
                details={
                    'name': party.name,
                    'party_type': party.party_type,
                },
            )

            messages.success(request, f"Party '{party.name}' ({party.get_party_type_display()}) added.")
        else:
            for field, errs in form.errors.items():
                messages.error(request, f"Party error: {errs.as_text()}")

        return redirect(f"{reverse('cases:case_detail', kwargs={'pk': pk})}#parties")


class PartyUpdateView(LoginRequiredMixin, ReadOnlyMixin, CaseAccessMixin, UpdateView):
    """
    Edit details of an existing case party.
    """
    model = Party
    form_class = PartyForm
    template_name = 'cases/party_form.html'
    pk_url_kwarg = 'party_id'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        party = self.get_object()
        require_case_access(self.request.user, party.case)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: PartyForm) -> HttpResponse:
        response = super().form_valid(form)
        party = self.object

        log_action(
            user=self.request.user,
            action='case.party.update',
            obj=party,
            case=party.case,
            request=self.request,
            details={
                'name': party.name,
                'party_type': party.party_type,
            },
        )

        messages.success(self.request, f"Party '{party.name}' updated successfully.")
        return response

    def get_success_url(self) -> str:
        return f"{reverse('cases:case_detail', kwargs={'pk': self.kwargs['pk']})}#parties"


class PartyDeleteView(LoginRequiredMixin, ReadOnlyMixin, CaseAccessMixin, DeleteView):
    """
    Delete a party record from a case.
    """
    model = Party
    template_name = 'cases/party_confirm_delete.html'
    pk_url_kwarg = 'party_id'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        party = self.get_object()
        require_case_access(self.request.user, party.case)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        party = self.get_object()
        case = party.case
        party_name = party.name
        party_type = party.get_party_type_display()

        response = super().delete(request, *args, **kwargs)

        log_action(
            user=request.user,
            action='case.party.delete',
            obj=case,
            case=case,
            request=request,
            details={
                'name': party_name,
                'party_type': party_type,
            },
        )

        messages.success(request, f"Party '{party_name}' removed from case.")
        return response

    def get_success_url(self) -> str:
        return f"{reverse('cases:case_detail', kwargs={'pk': self.kwargs['pk']})}#parties"


class CaseTimelineView(LoginRequiredMixin, CaseAccessMixin, View):
    """
    Merged chronological timeline of all events across a case:
    - Evidence intake & version updates
    - Custody transfer requests and acceptances
    - Court hearing dates & scheduled appearances
    - Task assignments & deadlines
    - Immutable audit log security events
    Returns HTML partial for AJAX dynamic loading or standalone rendering.
    """

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        case = get_object_or_404(Case, pk=pk)
        require_case_access(self.request.user, case)

        timeline_events = []

        # 1. Case Creation Event
        timeline_events.append({
            'timestamp': timezone.datetime.combine(case.opened_on, timezone.datetime.min.time(), tzinfo=timezone.utc),
            'event_type': 'case_created',
            'title': f'Case Initiated: {case.case_no}',
            'description': f'Case established with priority {case.get_priority_display()} ({case.get_case_type_display()}).',
            'actor': case.created_by.get_full_name() or case.created_by.email,
            'icon': 'bi-folder-plus',
            'marker_class': 'amber',
            'badge_label': 'Case Created',
        })

        # 2. Evidence Items
        for item in case.evidence_items.all().select_related('uploaded_by'):
            timeline_events.append({
                'timestamp': item.uploaded_at,
                'event_type': 'evidence_upload',
                'title': f'Evidence Lodged: {item.evidence_no}',
                'description': f"{item.title} (v{item.version}) - Hash: {item.sha256[:12]}...",
                'actor': item.uploaded_by.get_full_name() or item.uploaded_by.email,
                'icon': 'bi-shield-check',
                'marker_class': 'success' if item.status == Evidence.Status.ACTIVE else 'danger',
                'badge_label': f"Evidence v{item.version}",
                'link': reverse('evidence:evidence_detail', kwargs={'pk': item.pk}),
            })

        # 3. Custody Transfers
        for custody in CustodyEvent.objects.filter(evidence__case=case).select_related('evidence', 'from_user', 'to_user'):
            from_name = custody.from_user.get_full_name() if custody.from_user else 'Intake Vault'
            to_name = custody.to_user.get_full_name() if custody.to_user else 'Unknown'
            status_cls = 'success' if custody.status == CustodyEvent.Status.ACCEPTED else ('danger' if custody.status == CustodyEvent.Status.REJECTED else 'amber')
            timeline_events.append({
                'timestamp': custody.requested_at,
                'event_type': 'custody_transfer',
                'title': f'Custody Transfer: {custody.evidence.evidence_no}',
                'description': f"Transfer from {from_name} to {to_name}. Reason: {custody.reason}",
                'actor': from_name,
                'icon': 'bi-arrow-left-right',
                'marker_class': status_cls,
                'badge_label': f"Custody {custody.get_status_display()}",
            })

        # 4. Hearings
        for hearing in case.hearings.all().select_related('created_by'):
            timeline_events.append({
                'timestamp': hearing.hearing_date,
                'event_type': 'hearing',
                'title': f'Court Hearing: {hearing.court}',
                'description': f"Purpose: {hearing.purpose}. Outcome: {hearing.outcome or 'Pending'}",
                'actor': hearing.created_by.get_full_name() or hearing.created_by.email,
                'icon': 'bi-bank',
                'marker_class': 'amber',
                'badge_label': 'Hearing',
            })

        # 5. Tasks & Filing Deadlines
        for task in case.tasks.all().select_related('assigned_to'):
            timeline_events.append({
                'timestamp': task.due_date,
                'event_type': 'task_deadline',
                'title': f"Task Due: {task.title}",
                'description': f"Assigned to {task.assigned_to.get_full_name() or task.assigned_to.email}. Status: {task.get_status_display()}",
                'actor': task.assigned_to.get_full_name() or task.assigned_to.email,
                'icon': 'bi-calendar-check' if not task.is_filing_deadline else 'bi-alarm',
                'marker_class': 'danger' if task.status == Task.Status.OVERDUE else 'amber',
                'badge_label': 'Filing Deadline' if task.is_filing_deadline else 'Task Due',
            })

        # 6. Audit security records (notable actions)
        for log in AuditLog.objects.filter(case=case).select_related('user')[:30]:
            if log.action in ('case.create', 'evidence.upload'):
                continue  # already covered specifically
            actor_name = log.user.get_full_name() if log.user else 'System'
            timeline_events.append({
                'timestamp': log.timestamp,
                'event_type': 'audit',
                'title': f'Security Audit: {log.action}',
                'description': f"IP: {log.ip_address or 'Internal'} - Details: {str(log.details)[:120]}",
                'actor': actor_name,
                'icon': 'bi-journal-check',
                'marker_class': 'amber',
                'badge_label': log.action,
            })

        # Sort chronologically descending
        timeline_events.sort(key=lambda x: x['timestamp'], reverse=True)

        return render(
            request,
            'cases/partials/timeline_content.html',
            {
                'case': case,
                'timeline_events': timeline_events,
            },
        )
