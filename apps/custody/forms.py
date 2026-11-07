"""
Forms for the Custody app.
"""
from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.custody.models import CustodyEvent
from apps.evidence.models import Evidence


class CustodyTransferForm(forms.ModelForm):
    """
    Form to initiate a chain of custody transfer request.
    """
    to_user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Transfer To",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select an approved user to receive custody of this evidence."
    )
    reason = forms.CharField(
        label="Purpose / Justification",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Specify reason for transfer (e.g., Forensic Lab Examination, Court Presentation)...'
        }),
        help_text="Provide a clear, auditable justification for this custody change."
    )

    class Meta:
        model = CustodyEvent
        fields = ['to_user', 'reason']

    def __init__(self, *args, evidence: Evidence | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.evidence = evidence

        # Approved users only
        qs = User.objects.filter(is_approved=True, is_active=True).exclude(
            role=User.Role.REVIEWER
        )

        if evidence and evidence.current_holder_id:
            qs = qs.exclude(id=evidence.current_holder_id)

        self.fields['to_user'].queryset = qs
        self.fields['to_user'].label_from_instance = (
            lambda u: f"{u.get_full_name() or u.email} ({u.get_role_display()})"
        )


class CustodyResponseForm(forms.Form):
    """
    Form to accept or reject an incoming custody transfer request.
    """
    ACTION_CHOICES = [
        ('accept', 'Accept'),
        ('reject', 'Reject'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.HiddenInput()
    )
    reason = forms.CharField(
        required=False,
        label="Reason for Action",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter justification (mandatory if rejecting transfer)...'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        reason = cleaned_data.get('reason', '').strip()

        if action == 'reject' and not reason:
            self.add_error('reason', 'A reason is required when rejecting a custody transfer.')

        return cleaned_data
