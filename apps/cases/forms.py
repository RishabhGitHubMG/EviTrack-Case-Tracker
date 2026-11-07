"""
Forms for Case management, party registration, assignment, and filtering.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.cases.models import Case, CaseAssignment, Party

User = get_user_model()


class CaseCreateForm(forms.ModelForm):
    """
    Form to create a new Case. Status is automatically set to Open.
    """

    class Meta:
        model = Case
        fields = ['title', 'case_type', 'priority', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. State v. John Doe / Corporate IP Theft Investigation',
                'required': True,
            }),
            'case_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide comprehensive summary of case background, initial evidence context, and investigative focus...',
                'required': True,
            }),
        }

    def save(self, commit: bool = True) -> Case:
        instance = super().save(commit=False)
        instance.status = Case.Status.OPEN
        if commit:
            instance.save()
        return instance


class CaseUpdateForm(forms.ModelForm):
    """
    Form to edit case details and manage valid state machine transitions.
    Restricts status dropdown to only valid next steps from the case's current status.
    """

    class Meta:
        model = Case
        fields = ['title', 'case_type', 'status', 'priority', 'description', 'closed_on']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'case_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
            'closed_on': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            current_status = self.instance.status
            allowed_transitions = Case.VALID_TRANSITIONS.get(current_status, [])
            
            # Valid choices are the current status plus allowed next transitions
            available_choices = [(current_status, Case.Status(current_status).label)]
            for next_status in allowed_transitions:
                available_choices.append((next_status, Case.Status(next_status).label))
            
            self.fields['status'].choices = available_choices

            # If current status is archived or has no transitions, mark disabled or informative
            if not allowed_transitions:
                self.fields['status'].help_text = f"Case is in terminal state '{self.instance.get_status_display()}'. No further transitions allowed."

    def clean_status(self):
        new_status = self.cleaned_data.get('status')
        current_status = self.instance.status if self.instance else None
        if current_status and new_status != current_status:
            allowed = Case.VALID_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                raise ValidationError(
                    f"Invalid status transition from '{self.instance.get_status_display()}' "
                    f"to '{Case.Status(new_status).label}'. Allowed: {', '.join([Case.Status(s).label for s in allowed]) or 'None'}"
                )
        return new_status

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        closed_on = cleaned_data.get('closed_on')

        if status in [Case.Status.CLOSED, Case.Status.ARCHIVED] and not closed_on:
            cleaned_data['closed_on'] = timezone.now().date()

        return cleaned_data


class CaseAssignmentForm(forms.ModelForm):
    """
    Form to assign an approved user to a case with a designated role.
    """

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_approved=True).order_by('first_name', 'last_name', 'email'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select Approved User...",
    )

    class Meta:
        model = CaseAssignment
        fields = ['user', 'role_on_case']
        widgets = {
            'role_on_case': forms.Select(attrs={'class': 'form-select'}),
        }


class PartyForm(forms.ModelForm):
    """
    Form for adding and modifying case parties (complainant, accused, witness, client, counsel).
    """

    class Meta:
        model = Party
        fields = ['name', 'party_type', 'email', 'phone', 'address', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full legal or corporate entity name',
                'required': True,
            }),
            'party_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@example.com (optional)',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 000-0000 (optional)',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Physical address or official agency location (optional)',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Representation details, badge numbers, witness statements...',
            }),
        }


class CaseFilterForm(forms.Form):
    """
    Filter form for CaseListView supporting status, priority, type, and keyword search.
    """

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by case no or title...',
        }),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + list(Case.Status.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'All Priorities')] + list(Case.Priority.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    case_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(Case.CaseType.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
