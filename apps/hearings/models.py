from django.conf import settings
from django.db import models


class Hearing(models.Model):
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='hearings',
    )
    hearing_date = models.DateTimeField()
    court = models.CharField(max_length=200)
    purpose = models.CharField(max_length=300)
    outcome = models.TextField(blank=True)
    next_hearing_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_hearings',
    )

    class Meta:
        db_table = 'hearings_hearing'
        verbose_name = 'Hearing'
        verbose_name_plural = 'Hearings'
        ordering = ['hearing_date']
        indexes = [
            models.Index(fields=['hearing_date']),
            models.Index(fields=['case']),
        ]

    def __str__(self) -> str:
        return f'{self.case.case_no} - Hearing on {self.hearing_date:%Y-%m-%d} at {self.court}'


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        OVERDUE = 'overdue', 'Overdue'

    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_tasks',
    )
    due_date = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    is_filing_deadline = models.BooleanField(
        default=False,
        help_text='Indicates if this task represents a strict court filing deadline',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tasks',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'hearings_task'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['due_date', '-id']
        indexes = [
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self) -> str:
        return f'{self.title} ({self.get_status_display()}) - {self.case.case_no}'
