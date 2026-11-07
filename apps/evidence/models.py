from django.conf import settings
from django.db import models
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'evidence_tag'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Evidence(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        FLAGGED = 'flagged', 'Flagged'
        ARCHIVED = 'archived', 'Archived'
        DELETED = 'deleted', 'Deleted'

    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='evidence_items',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='evidence_items')
    evidence_no = models.CharField(max_length=32, unique=True, blank=True)
    file_path = models.CharField(
        max_length=500,
        help_text='Path relative to EVIDENCE_ROOT outside web root',
    )
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField(help_text='File size in bytes')
    sha256 = models.CharField(max_length=64, help_text='SHA-256 hex digest')
    version = models.PositiveIntegerField(default=1)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='newer_versions',
        help_text='Previous version of this evidence item',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_evidence',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    current_holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='held_evidence',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    is_latest_version = models.BooleanField(default=True)

    class Meta:
        db_table = 'evidence_item'
        verbose_name = 'Evidence'
        verbose_name_plural = 'Evidence Items'
        ordering = ['-uploaded_at', '-id']
        indexes = [
            models.Index(fields=['evidence_no']),
            models.Index(fields=['sha256']),
            models.Index(fields=['status']),
            models.Index(fields=['case']),
            models.Index(fields=['uploaded_at']),
        ]

    def __str__(self) -> str:
        return f'{self.evidence_no} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.evidence_no:
            year = timezone.now().year
            prefix = f"EV-{year}-"
            last_item = (
                Evidence.objects.filter(evidence_no__startswith=prefix)
                .order_by('-evidence_no')
                .first()
            )
            if last_item and last_item.evidence_no:
                try:
                    last_seq = int(last_item.evidence_no.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            self.evidence_no = f"{prefix}{new_seq:05d}"

        if not self.current_holder and self.uploaded_by_id:
            self.current_holder = self.uploaded_by

        super().save(*args, **kwargs)

        if self.parent_id and self.is_latest_version:
            Evidence.objects.filter(pk=self.parent_id).update(is_latest_version=False)


class IntegrityCheck(models.Model):
    class Result(models.TextChoices):
        VERIFIED = 'verified', 'Verified'
        MODIFIED = 'modified', 'Modified'

    evidence = models.ForeignKey(
        Evidence, on_delete=models.CASCADE, related_name='integrity_checks'
    )
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='integrity_checks_performed',
    )
    result = models.CharField(max_length=20, choices=Result.choices)
    computed_hash = models.CharField(max_length=64)
    stored_hash = models.CharField(max_length=64)
    checked_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evidence_integrity_check'
        verbose_name = 'Integrity Check'
        verbose_name_plural = 'Integrity Checks'
        ordering = ['-checked_on']
        indexes = [
            models.Index(fields=['evidence']),
            models.Index(fields=['checked_on']),
        ]

    def __str__(self) -> str:
        return f'{self.evidence.evidence_no} - {self.get_result_display()} ({self.checked_on:%Y-%m-%d %H:%M})'
