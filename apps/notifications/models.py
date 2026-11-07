from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Reminder(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'
        INAPP = 'inapp', 'In-App'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        ESCALATED = 'escalated', 'Escalated'

    target_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='reminders',
    )
    target_id = models.PositiveBigIntegerField()
    target = GenericForeignKey('target_type', 'target_id')

    remind_at = models.DateTimeField()
    channel = models.CharField(
        max_length=20, choices=Channel.choices, default=Channel.EMAIL
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    last_error = models.TextField(blank=True)
    dedup_key = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique key target+time+channel to prevent duplicate reminder queuing',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reminders',
        help_text='Recipient user of reminder',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications_reminder'
        verbose_name = 'Reminder'
        verbose_name_plural = 'Reminders'
        ordering = ['remind_at']
        indexes = [
            models.Index(fields=['remind_at']),
            models.Index(fields=['status']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self) -> str:
        return f'Reminder for {self.user} via {self.get_channel_display()} at {self.remind_at} ({self.get_status_display()})'


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        INFO = 'info', 'Info'
        SUCCESS = 'success', 'Success'
        WARNING = 'warning', 'Warning'
        DANGER = 'danger', 'Danger'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications_notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        snippet = (
            (self.message[:40] + '...')
            if len(self.message) > 40
            else self.message
        )
        return f'Notification ({self.user}): {snippet}'
