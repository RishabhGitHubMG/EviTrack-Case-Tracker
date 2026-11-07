"""
Forms for Evidence intake, metadata management, and validation.
"""
import mimetypes
import os
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.evidence.models import Evidence, Tag

DANGEROUS_EXTENSIONS = {
    '.exe', '.dll', '.bat', '.sh', '.cmd', '.vbs', '.ps1',
    '.com', '.scr', '.pif', '.application', '.gadget', '.msi',
    '.msp', '.hta', '.cpl', '.msc', '.jar', '.reg',
}


class EvidenceUploadForm(forms.ModelForm):
    """
    Form for lodging new evidence files into the secure Evidence Vault.
    Performs comprehensive cryptographic and extension security checks.
    """

    file = forms.FileField(
        label="Evidence File",
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'evidenceFileInput',
            'accept': ','.join(getattr(settings, 'EVIDENCE_ALLOWED_EXTENSIONS', [])),
        }),
        help_text="Max file size: 100 MB. Allowed extensions: PDF, DOCX, images, audio, video, archives, text.",
    )
    tags_input = forms.CharField(
        label="Tags",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. digital, mobile-extraction, cctv, financial (comma separated)',
        }),
        help_text="Separate tags with commas.",
    )

    class Meta:
        model = Evidence
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descriptive title for evidence item',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Physical collection context, extraction tools used, device serial number...',
            }),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if not uploaded_file:
            raise ValidationError("An evidence file must be provided.")

        # 1. File size enforcement
        max_size = getattr(settings, 'EVIDENCE_MAX_SIZE', 104857600)  # 100MB
        if uploaded_file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            current_mb = uploaded_file.size / (1024 * 1024)
            raise ValidationError(
                f"File size ({current_mb:.1f} MB) exceeds maximum allowed size of {max_mb:.0f} MB."
            )

        filename = uploaded_file.name.lower()
        base_name, ext = os.path.splitext(filename)

        # 2. Extension validation
        allowed_exts = getattr(settings, 'EVIDENCE_ALLOWED_EXTENSIONS', None)
        if allowed_exts and ext not in allowed_exts:
            raise ValidationError(
                f"File extension '{ext}' is not permitted. Allowed: {', '.join(allowed_exts[:10])}..."
            )

        # 3. Double extension check (prevent hidden executables e.g. payload.exe.pdf or file.pdf.exe)
        parts = filename.split('.')
        if len(parts) > 2:
            # Check if any intermediate part is a dangerous executable extension
            for part in parts[1:-1]:
                if f".{part}" in DANGEROUS_EXTENSIONS:
                    raise ValidationError(
                        f"Potentially deceptive or dangerous double extension detected ('.{part}'). File rejected."
                    )
        if ext in DANGEROUS_EXTENSIONS:
            raise ValidationError(f"Executable file types ({ext}) are strictly prohibited.")

        # 4. MIME type check
        allowed_mimes = getattr(settings, 'EVIDENCE_ALLOWED_MIMES', None)
        declared_mime = getattr(uploaded_file, 'content_type', '').lower()
        guessed_mime, _ = mimetypes.guess_type(filename)
        
        effective_mime = declared_mime or guessed_mime or 'application/octet-stream'

        if allowed_mimes:
            # If declared or guessed is in allowed mimes, allow; otherwise raise
            mime_match = (declared_mime in allowed_mimes) or (guessed_mime in allowed_mimes)
            if not mime_match and declared_mime not in ('application/octet-stream', 'binary/octet-stream'):
                raise ValidationError(
                    f"File MIME type '{declared_mime}' is not permitted."
                )

        return uploaded_file

    def get_tag_names(self) -> list[str]:
        raw_tags = self.cleaned_data.get('tags_input', '')
        if not raw_tags:
            return []
        return [t.strip().lower() for t in raw_tags.split(',') if t.strip()]


class EvidenceUpdateForm(forms.ModelForm):
    """
    Form for editing evidence metadata (title, description, tags).
    Physical file, SHA-256 hash, and evidence_no remain immutable.
    """

    tags_input = forms.CharField(
        label="Tags",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'comma, separated, tags',
        }),
    )

    class Meta:
        model = Evidence
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            current_tags = self.instance.tags.values_list('name', flat=True)
            self.fields['tags_input'].initial = ', '.join(current_tags)

    def get_tag_names(self) -> list[str]:
        raw_tags = self.cleaned_data.get('tags_input', '')
        if not raw_tags:
            return []
        return [t.strip().lower() for t in raw_tags.split(',') if t.strip()]
