import hashlib
import json
from typing import Any

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class ChainVerificationResult:
    """
    Result object returned by AuditLog.verify_chain.
    Compatible with boolean checks, tuple unpacking, and dictionary/attribute access.
    """

    def __init__(
        self,
        is_valid: bool,
        verified_count: int,
        error: str = '',
        errors: list[str] | None = None,
    ):
        self.is_valid = is_valid
        self.verified_count = verified_count
        self.error = error
        self.errors = errors or ([] if is_valid else [error])

    def __bool__(self) -> bool:
        return self.is_valid

    def __iter__(self):
        return iter((self.is_valid, self.error))

    def __getitem__(self, item: Any) -> Any:
        if item in ('is_valid', 0):
            return self.is_valid
        if item in ('error', 1):
            return self.error
        if item == 'verified_count':
            return self.verified_count
        if item == 'errors':
            return self.errors
        raise KeyError(item)

    def __repr__(self) -> str:
        return (
            f"<ChainVerificationResult valid={self.is_valid} "
            f"count={self.verified_count} error={self.error!r}>"
        )


class AuditLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise TypeError('Audit logs cannot be modified')

    def delete(self):
        raise TypeError('Audit logs cannot be deleted')


class AuditLog(models.Model):
    objects = AuditLogQuerySet.as_manager()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='audit_logs',
        help_text='Actor performing the action (null for automated system events)',
    )
    action = models.CharField(
        max_length=100,
        help_text="Standardized dot-notation action (e.g. 'evidence.upload', 'case.create')",
    )
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        help_text='Content type of the target entity',
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='Primary key or identifier of the target entity',
    )
    case = models.ForeignKey(
        'cases.Case',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='audit_entries',
        help_text='Case context associated with this log entry',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)
    prev_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text='SHA-256 hash of previous audit log entry',
    )
    entry_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text='SHA-256 hash of this audit log entry including prev_hash',
    )

    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['case']),
        ]

    def __str__(self) -> str:
        actor = self.user.email if self.user else 'SYSTEM'
        return f'[{self.timestamp:%Y-%m-%d %H:%M:%S}] {actor} -> {self.action}'

    def calculate_hash(self) -> str:
        """
        Computes SHA-256 hash over log entry fields and prev_hash.
        """
        ts_str = self.timestamp.isoformat() if self.timestamp else ''
        payload = (
            f"{self.prev_hash}:"
            f"{ts_str}:"
            f"{self.user_id or ''}:"
            f"{self.action}:"
            f"{self.content_type_id or ''}:"
            f"{self.object_id or ''}:"
            f"{self.case_id or ''}:"
            f"{self.ip_address or ''}:"
            f"{self.user_agent or ''}:"
            f"{json.dumps(self.details or {}, sort_keys=True, separators=(',', ':'))}"
        )
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        # Enforce append-only / immutable audit records
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError('Audit logs cannot be modified')

        if not self.timestamp:
            self.timestamp = timezone.now()

        if not self.prev_hash:
            latest = AuditLog.objects.order_by('-pk').first()
            self.prev_hash = latest.entry_hash if latest and latest.entry_hash else ('0' * 64)

        field = self._meta.get_field('timestamp')
        original_auto_now_add = field.auto_now_add
        try:
            field.auto_now_add = False
            self.entry_hash = self.calculate_hash()
            super().save(*args, **kwargs)
        finally:
            field.auto_now_add = original_auto_now_add

    def delete(self, *args, **kwargs):
        raise ValueError('Audit logs cannot be deleted')

    @classmethod
    def verify_chain(cls, limit: int = 1000) -> ChainVerificationResult:
        """
        Verifies the cryptographic hash chain of the last `limit` audit log entries.
        Returns a ChainVerificationResult containing is_valid, verified_count, and error details.
        """
        entries = list(cls.objects.order_by('-id')[:limit])
        if not entries:
            return ChainVerificationResult(is_valid=True, verified_count=0)

        entries.reverse()
        errors: list[str] = []

        # Check whether the first entry in our slice links to a prior DB entry
        first_entry = entries[0]
        prior_entry = cls.objects.filter(id__lt=first_entry.id).order_by('-id').first()
        if prior_entry:
            if first_entry.prev_hash != prior_entry.entry_hash:
                errors.append(
                    f"Entry ID {first_entry.id} prev_hash mismatch: expected {prior_entry.entry_hash}, got {first_entry.prev_hash}"
                )
        elif first_entry.prev_hash != ('0' * 64):
            # Genesis record must link to genesis zero hash
            errors.append(
                f"Genesis Entry ID {first_entry.id} prev_hash mismatch: expected {'0'*64}, got {first_entry.prev_hash}"
            )

        for i, entry in enumerate(entries):
            # Verify self hash
            expected_hash = entry.calculate_hash()
            if entry.entry_hash != expected_hash:
                errors.append(
                    f"Entry ID {entry.id} tampered: stored {entry.entry_hash}, computed {expected_hash}"
                )

            # Verify chain linkage to preceding entry in this slice
            if i > 0:
                prev = entries[i - 1]
                if entry.prev_hash != prev.entry_hash:
                    errors.append(
                        f"Entry ID {entry.id} chain break: prev_hash {entry.prev_hash} != Entry {prev.id} hash {prev.entry_hash}"
                    )

        if errors:
            return ChainVerificationResult(
                is_valid=False,
                verified_count=len(entries),
                error=errors[0],
                errors=errors,
            )

        return ChainVerificationResult(is_valid=True, verified_count=len(entries))
