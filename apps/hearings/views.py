"""
Views for Hearings, Tasks, and Calendar modules.
"""
from datetime import datetime, timedelta
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.mixins import CaseAccessMixin, check_case_access, get_user_accessible_cases
from apps.cases.models import Case
from apps.hearings.forms import HearingForm, HearingOutcomeForm, TaskForm, TaskStatusForm
from apps.hearings.models import Hearing, Task
from apps.hearings.services import (
    cancel_pending_reminders,
    check_overdue_tasks,
    create_hearing,
    create_task,
    schedule_hearing_reminders,
    schedule_task_reminders,
    update_hearing,
)


def _get_client_ip(request: HttpRequest) -> str | None:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class HearingListView(LoginRequiredMixin, ListView):
    """
    List court hearings for cases accessible to the current user,
    with filtering by upcoming, past, and case.
    """
    model = Hearing
    template_name = 'hearings/hearing_list.html'
    context_object_name = 'hearings'
    paginate_by = 25

    def get_queryset(self):
        accessible_cases = get_user_accessible_cases(self.request.user)
        qs = (
            Hearing.objects.filter(case__in=accessible_cases)
            .select_related('case', 'created_by')
            .order_by('hearing_date')
        )

        filter_type = self.request.GET.get('filter', 'upcoming')
        now = timezone.now()

        if filter_type == 'upcoming':
            qs = qs.filter(hearing_date__gte=now)
        elif filter_type == 'past':
            qs = qs.filter(hearing_date__lt=now).order_by('-hearing_date')

        case_filter = self.request.GET.get('case')
        if case_filter:
            qs = qs.filter(case__case_no__icontains=case_filter)

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        accessible_cases = get_user_accessible_cases(self.request.user)
        now = timezone.now()

        context.update({
            'current_filter': self.request.GET.get('filter', 'upcoming'),
            'case_filter': self.request.GET.get('case', ''),
            'upcoming_count': Hearing.objects.filter(case__in=accessible_cases, hearing_date__gte=now).count(),
            'past_count': Hearing.objects.filter(case__in=accessible_cases, hearing_date__lt=now).count(),
            'accessible_cases': accessible_cases,
        })
        return context


class HearingCreateView(CaseAccessMixin, View):
    """
    Schedules a court hearing for a given case.
    """
    template_name = 'hearings/hearing_create.html'

    def get_case(self) -> Case:
        case_id = self.kwargs.get('case_id')
        case = get_object_or_404(Case, pk=case_id)
        if self.request.user.is_reviewer or not check_case_access(self.request.user, case):
            raise PermissionDenied("You do not have access to this case.")
        return case

    def get(self, request: HttpRequest, case_id: int) -> HttpResponse:
        case = self.get_case()
        initial = {}
        selected_date = parse_datetime(request.GET.get('date', ''))
        if selected_date:
            if timezone.is_aware(selected_date):
                selected_date = timezone.localtime(selected_date)
            initial['hearing_date'] = selected_date.strftime('%Y-%m-%dT%H:%M')
        form = HearingForm(case=case, initial=initial)
        return render(request, self.template_name, {
            'form': form,
            'case': case,
        })

    def post(self, request: HttpRequest, case_id: int) -> HttpResponse:
        case = self.get_case()
        form = HearingForm(request.POST, case=case)

        if form.is_valid():
            ip_addr = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            hearing = create_hearing(
                case=case,
                data=form.cleaned_data,
                user=request.user,
                ip_address=ip_addr,
                user_agent=user_agent,
            )

            messages.success(
                request,
                f"Hearing scheduled for {hearing.hearing_date:%B %d, %Y at %H:%M} at {hearing.court}."
            )

            # If next_hearing_date provided, notify and offer quick link
            if hearing.next_hearing_date:
                messages.info(
                    request,
                    f"A subsequent hearing is noted for {hearing.next_hearing_date:%B %d, %Y}. Remember to schedule it once proceedings conclude."
                )

            return redirect('hearings:hearing_detail', pk=hearing.pk)

        return render(request, self.template_name, {
            'form': form,
            'case': case,
        })


class HearingDetailView(CaseAccessMixin, DetailView):
    """
    Displays hearing proceedings, outcome, judicial remarks, and exhibits.
    """
    model = Hearing
    template_name = 'hearings/hearing_detail.html'
    context_object_name = 'hearing'

    def get_object(self, queryset=None) -> Hearing:
        hearing = super().get_object(queryset)
        if not check_case_access(self.request.user, hearing.case):
            raise PermissionDenied("You do not have access to this case.")
        return hearing

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        hearing = self.object
        context.update({
            'case': hearing.case,
            'reminders': hearing.case.hearings.filter(pk=hearing.pk).first(),
            'outcome_form': HearingOutcomeForm(instance=hearing),
        })
        return context


class HearingUpdateView(CaseAccessMixin, View):
    """
    Edits an existing hearing with auto reminder rescheduling on date modification.
    """
    template_name = 'hearings/hearing_update.html'

    def get_hearing(self) -> Hearing:
        pk = self.kwargs.get('pk')
        hearing = get_object_or_404(Hearing.objects.select_related('case'), pk=pk)
        if self.request.user.is_reviewer or not check_case_access(self.request.user, hearing.case):
            raise PermissionDenied("You do not have access to this case.")
        return hearing

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        hearing = self.get_hearing()
        form = HearingForm(instance=hearing, case=hearing.case)
        return render(request, self.template_name, {
            'form': form,
            'hearing': hearing,
            'case': hearing.case,
        })

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        hearing = self.get_hearing()
        form = HearingForm(request.POST, instance=hearing, case=hearing.case)

        if form.is_valid():
            ip_addr = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            update_hearing(
                hearing=hearing,
                data=form.cleaned_data,
                user=request.user,
                ip_address=ip_addr,
                user_agent=user_agent,
            )

            messages.success(request, f"Hearing details updated successfully.")
            return redirect('hearings:hearing_detail', pk=hearing.pk)

        return render(request, self.template_name, {
            'form': form,
            'hearing': hearing,
            'case': hearing.case,
        })


class HearingOutcomeView(CaseAccessMixin, View):
    """
    Convenience view to record or update hearing outcome and set subsequent court date.
    """
    template_name = 'hearings/hearing_detail.html'

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        hearing = get_object_or_404(Hearing.objects.select_related('case'), pk=pk)
        if request.user.is_reviewer or not check_case_access(request.user, hearing.case):
            raise PermissionDenied("You do not have access to this case.")

        form = HearingOutcomeForm(request.POST, instance=hearing)
        if form.is_valid():
            hearing.outcome = form.cleaned_data['outcome']
            hearing.next_hearing_date = form.cleaned_data.get('next_hearing_date')
            hearing.save(update_fields=['outcome', 'next_hearing_date'])

            messages.success(request, "Hearing outcome recorded successfully.")
            return redirect('hearings:hearing_detail', pk=hearing.pk)

        messages.error(request, "Please check the form inputs.")
        return redirect('hearings:hearing_detail', pk=hearing.pk)


class TaskListView(LoginRequiredMixin, ListView):
    """
    List all tasks accessible to user with status tabs (All, Pending, Overdue, Completed).
    """
    model = Task
    template_name = 'hearings/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 25

    def get_queryset(self):
        # Scan and mark overdue tasks first
        check_overdue_tasks()

        accessible_cases = get_user_accessible_cases(self.request.user)
        qs = (
            Task.objects.filter(case__in=accessible_cases)
            .select_related('case', 'assigned_to', 'created_by')
            .order_by('due_date')
        )

        status_tab = self.request.GET.get('status', 'all')
        if status_tab == 'pending':
            qs = qs.filter(status=Task.Status.PENDING)
        elif status_tab == 'in_progress':
            qs = qs.filter(status=Task.Status.IN_PROGRESS)
        elif status_tab == 'overdue':
            qs = qs.filter(status=Task.Status.OVERDUE)
        elif status_tab == 'completed':
            qs = qs.filter(status=Task.Status.COMPLETED).order_by('-completed_at', '-due_date')

        case_filter = self.request.GET.get('case')
        if case_filter:
            qs = qs.filter(case__case_no__icontains=case_filter)

        my_tasks_only = self.request.GET.get('mine')
        if my_tasks_only == '1':
            qs = qs.filter(assigned_to=self.request.user)

        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        accessible_cases = get_user_accessible_cases(self.request.user)
        base_qs = Task.objects.filter(case__in=accessible_cases)

        context.update({
            'current_status': self.request.GET.get('status', 'all'),
            'case_filter': self.request.GET.get('case', ''),
            'my_tasks_only': self.request.GET.get('mine', '') == '1',
            'count_all': base_qs.count(),
            'count_pending': base_qs.filter(status=Task.Status.PENDING).count(),
            'count_in_progress': base_qs.filter(status=Task.Status.IN_PROGRESS).count(),
            'count_overdue': base_qs.filter(status=Task.Status.OVERDUE).count(),
            'count_completed': base_qs.filter(status=Task.Status.COMPLETED).count(),
            'accessible_cases': accessible_cases,
        })
        return context


class TaskCreateView(CaseAccessMixin, View):
    """
    Creates a new task for an accessible case.
    """
    template_name = 'hearings/task_create.html'

    def get_case(self) -> Case:
        case_id = self.kwargs.get('case_id')
        case = get_object_or_404(Case, pk=case_id)
        if not check_case_access(self.request.user, case):
            raise PermissionDenied("You do not have access to this case.")
        return case

    def get(self, request: HttpRequest, case_id: int) -> HttpResponse:
        case = self.get_case()
        form = TaskForm(case=case)
        return render(request, self.template_name, {
            'form': form,
            'case': case,
        })

    def post(self, request: HttpRequest, case_id: int) -> HttpResponse:
        case = self.get_case()
        form = TaskForm(request.POST, case=case)

        if form.is_valid():
            ip_addr = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            task = create_task(
                case=case,
                data=form.cleaned_data,
                user=request.user,
                ip_address=ip_addr,
                user_agent=user_agent,
            )

            messages.success(request, f"Task '{task.title}' created and assigned.")
            return redirect('hearings:task_list')

        return render(request, self.template_name, {
            'form': form,
            'case': case,
        })


class TaskUpdateView(CaseAccessMixin, View):
    """
    Edits a task and updates deadline reminders.
    """
    template_name = 'hearings/task_update.html'

    def get_task(self) -> Task:
        pk = self.kwargs.get('pk')
        task = get_object_or_404(Task.objects.select_related('case'), pk=pk)
        if not check_case_access(self.request.user, task.case):
            raise PermissionDenied("You do not have access to this task's case.")
        return task

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        task = self.get_task()
        form = TaskForm(instance=task, case=task.case)
        return render(request, self.template_name, {
            'form': form,
            'task': task,
            'case': task.case,
        })

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        task = self.get_task()
        old_due_date = task.due_date
        form = TaskForm(request.POST, instance=task, case=task.case)

        if form.is_valid():
            updated_task = form.save()

            if old_due_date != updated_task.due_date:
                cancel_pending_reminders(updated_task)
                schedule_task_reminders(updated_task)

            messages.success(request, f"Task '{updated_task.title}' updated.")
            return redirect('hearings:task_list')

        return render(request, self.template_name, {
            'form': form,
            'task': task,
            'case': task.case,
        })


class TaskStatusUpdateView(CaseAccessMixin, View):
    """
    AJAX endpoint to update task status (Pending, In Progress, Completed, Overdue).
    """

    def post(self, request: HttpRequest, pk: int) -> JsonResponse:
        task = get_object_or_404(Task.objects.select_related('case'), pk=pk)
        if not check_case_access(request.user, task.case):
            return JsonResponse({'error': 'Permission denied.'}, status=403)

        new_status = request.POST.get('status')
        if not new_status or new_status not in Task.Status.values:
            return JsonResponse({'error': 'Invalid status provided.'}, status=400)

        task.status = new_status
        if new_status == Task.Status.COMPLETED:
            task.completed_at = timezone.now()
            cancel_pending_reminders(task)
        else:
            task.completed_at = None
            if new_status in (Task.Status.PENDING, Task.Status.IN_PROGRESS):
                schedule_task_reminders(task)

        task.save(update_fields=['status', 'completed_at'])

        return JsonResponse({
            'success': True,
            'task_id': task.pk,
            'status': task.status,
            'status_display': task.get_status_display(),
            'is_completed': (task.status == Task.Status.COMPLETED),
        })


class CalendarView(LoginRequiredMixin, TemplateView):
    """
    Interactive full calendar view visualizing hearings, tasks, and filing deadlines.
    """
    template_name = 'hearings/calendar.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        accessible_cases = get_user_accessible_cases(self.request.user)
        context.update({
            'accessible_cases': accessible_cases,
            'can_manage_hearings': not self.request.user.is_reviewer,
        })
        return context


class CalendarEventsAPIView(APIView):
    """
    DRF APIView returning JSON events for FullCalendar.
    Returns:
    - Hearings: Navy (#14213D)
    - Tasks: Amber (#F2A900)
    - Filing Deadlines: Red (#DC2626)
    Filtered by user accessible cases and start/end date range parameters.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest, format=None) -> Response:
        accessible_cases = get_user_accessible_cases(request.user)

        start_param = request.GET.get('start')
        end_param = request.GET.get('end')

        hearings_qs = (
            Hearing.objects.filter(case__in=accessible_cases)
            .select_related('case')
        )
        tasks_qs = (
            Task.objects.filter(case__in=accessible_cases)
            .select_related('case', 'assigned_to')
        )

        if start_param:
            try:
                start_dt = parse_datetime(start_param)
                if not start_dt:
                    start_dt = datetime.fromisoformat(start_param.replace('Z', '+00:00'))
                hearings_qs = hearings_qs.filter(hearing_date__gte=start_dt)
                tasks_qs = tasks_qs.filter(due_date__gte=start_dt)
            except Exception:
                pass

        if end_param:
            try:
                end_dt = parse_datetime(end_param)
                if not end_dt:
                    end_dt = datetime.fromisoformat(end_param.replace('Z', '+00:00'))
                hearings_qs = hearings_qs.filter(hearing_date__lte=end_dt)
                tasks_qs = tasks_qs.filter(due_date__lte=end_dt)
            except Exception:
                pass

        events = []

        # 1. Hearings (Navy color: #14213D)
        for h in hearings_qs:
            end_time = h.hearing_date + timedelta(hours=2)
            events.append({
                'id': f"hearing-{h.pk}",
                'title': f"⚖️ {h.case.case_no}: {h.purpose} ({h.court})",
                'start': h.hearing_date.isoformat(),
                'end': end_time.isoformat(),
                'color': '#14213D',
                'textColor': '#FFFFFF',
                'url': reverse('hearings:hearing_detail', kwargs={'pk': h.pk}),
                'extendedProps': {
                    'type': 'hearing',
                    'case_no': h.case.case_no,
                    'court': h.court,
                    'status': 'scheduled',
                }
            })

        # 2. Tasks & Strict Deadlines
        for t in tasks_qs:
            is_deadline = t.is_filing_deadline
            color = '#DC2626' if is_deadline else '#F2A900'
            text_color = '#FFFFFF' if is_deadline else '#14213D'
            prefix = "🚨 DEADLINE" if is_deadline else "📋 TASK"

            events.append({
                'id': f"task-{t.pk}",
                'title': f"{prefix} [{t.case.case_no}]: {t.title}",
                'start': t.due_date.isoformat(),
                'end': t.due_date.isoformat(),
                'allDay': False,
                'color': color,
                'textColor': text_color,
                'url': reverse('hearings:task_update', kwargs={'pk': t.pk}),
                'extendedProps': {
                    'type': 'deadline' if is_deadline else 'task',
                    'case_no': t.case.case_no,
                    'assigned_to': t.assigned_to.get_full_name() or t.assigned_to.email,
                    'status': t.status,
                }
            })

        return Response(events)
