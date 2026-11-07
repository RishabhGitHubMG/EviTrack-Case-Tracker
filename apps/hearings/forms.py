"""
Forms for the Hearings and Tasks module.
"""
from django import forms
from django.db.models import Q

from apps.accounts.models import User
from apps.cases.models import Case
from apps.hearings.models import Hearing, Task


class HearingForm(forms.ModelForm):
    """
    Form to schedule or update a court hearing.
    """
    case = forms.ModelChoiceField(
        queryset=Case.objects.all(),
        widget=forms.HiddenInput()
    )
    hearing_date = forms.DateTimeField(
        label="Hearing Date & Time",
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )
    court = forms.CharField(
        max_length=200,
        label="Court / Jurisdiction",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. District Court, Courtroom 4B / High Court'
        })
    )
    purpose = forms.CharField(
        max_length=300,
        label="Purpose / Motion",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Preliminary Hearing, Evidence Admissibility, Bail Arguments'
        })
    )
    outcome = forms.CharField(
        required=False,
        label="Outcome / Ruling",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Record judge remarks, rulings, or proceedings summary...'
        })
    )
    next_hearing_date = forms.DateTimeField(
        required=False,
        label="Next Hearing Date & Time",
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )
    notes = forms.CharField(
        required=False,
        label="Internal Case Notes",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Internal strategy notes, exhibits required, or witness prep details...'
        })
    )

    class Meta:
        model = Hearing
        fields = [
            'case',
            'hearing_date',
            'court',
            'purpose',
            'outcome',
            'next_hearing_date',
            'notes',
        ]

    def __init__(self, *args, case: Case | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if case:
            self.fields['case'].initial = case
        if self.instance and self.instance.pk:
            if self.instance.hearing_date:
                self.initial['hearing_date'] = self.instance.hearing_date.strftime('%Y-%m-%dT%H:%M')
            if self.instance.next_hearing_date:
                self.initial['next_hearing_date'] = self.instance.next_hearing_date.strftime('%Y-%m-%dT%H:%M')


class HearingOutcomeForm(forms.ModelForm):
    """
    Focused form to record hearing outcome and schedule next hearing date.
    """
    outcome = forms.CharField(
        label="Hearing Outcome / Summary of Proceedings",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter comprehensive court outcome, judicial directives, orders, or bail decisions...'
        })
    )
    next_hearing_date = forms.DateTimeField(
        required=False,
        label="Subsequent Hearing Date & Time (Optional)",
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )

    class Meta:
        model = Hearing
        fields = ['outcome', 'next_hearing_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.next_hearing_date:
            self.initial['next_hearing_date'] = self.instance.next_hearing_date.strftime('%Y-%m-%dT%H:%M')


class TaskForm(forms.ModelForm):
    """
    Form to create or edit an investigative or legal task.
    """
    case = forms.ModelChoiceField(
        queryset=Case.objects.all(),
        widget=forms.HiddenInput()
    )
    title = forms.CharField(
        max_length=200,
        label="Task Title",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. File Affidavit of Service, Forensic Extraction of Drive'
        })
    )
    description = forms.CharField(
        required=False,
        label="Detailed Instructions",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Specific steps, evidentiary requirements, and compliance checklists...'
        })
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Assignee",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    due_date = forms.DateTimeField(
        label="Due Date & Time",
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
    )
    is_filing_deadline = forms.BooleanField(
        required=False,
        label="Strict Court Filing Deadline",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Flag this task with critical priority and strict statutory filing reminders."
    )

    class Meta:
        model = Task
        fields = [
            'case',
            'title',
            'description',
            'assigned_to',
            'due_date',
            'is_filing_deadline',
        ]

    def __init__(self, *args, case: Case | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        target_case = case or (self.instance.case if self.instance and self.instance.pk else None)
        if target_case:
            self.fields['case'].initial = target_case
            # Assigned users on this case, case creator, or active case managers/investigators
            qs = User.objects.filter(
                Q(case_assignments__case=target_case) |
                Q(id=target_case.created_by_id) |
                Q(role__in=[User.Role.ADMIN, User.Role.CASE_MANAGER, User.Role.INVESTIGATOR]),
                is_active=True,
                is_approved=True
            ).exclude(role=User.Role.REVIEWER).distinct()
        else:
            qs = User.objects.filter(is_active=True, is_approved=True).exclude(role=User.Role.REVIEWER)

        self.fields['assigned_to'].queryset = qs
        self.fields['assigned_to'].label_from_instance = (
            lambda u: f"{u.get_full_name() or u.email} ({u.get_role_display()})"
        )

        if self.instance and self.instance.pk and self.instance.due_date:
            self.initial['due_date'] = self.instance.due_date.strftime('%Y-%m-%dT%H:%M')


class TaskStatusForm(forms.ModelForm):
    """
    Form to quickly update task status.
    """
    status = forms.ChoiceField(
        choices=Task.Status.choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Task
        fields = ['status']
