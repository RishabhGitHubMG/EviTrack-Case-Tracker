from django.conf import settings
from django.db import models


class CustodyEvent(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'

    evidence = models.ForeignKey(
        'evidence.Evidence',
        on_delete=models.CASCADE,
        related_name='custody_events',
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='custody_transfers_out',
        help_text='User transferring custody (null for initial intake)',
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='custody_transfers_in',
        help_text='Recipient user of custody transfer',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.REQUESTED
    )
    reason = models.TextField(help_text='Purpose or justification for transfer')
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='custody_resolutions',
    )

    class Meta:
        db_table = 'custody_event'
        verbose_name = 'Custody Event'
        verbose_name_plural = 'Custody Events'
        ordering = ['-requested_at', '-id']
        indexes = [
            models.Index(fields=['evidence']),
            models.Index(fields=['status']),
            models.Index(fields=['requested_at']),
        ]

    def __str__(self) -> str:
        from_display = self.from_user if self.from_user else 'Initial Intake'
        return f'{self.evidence.evidence_no}: {from_display} -> {self.to_user} ({self.get_status_display()})'
