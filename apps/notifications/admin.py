from django.contrib import admin

from apps.notifications.models import Notification, Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'channel',
        'status',
        'remind_at',
        'attempts',
        'max_attempts',
        'dedup_key',
        'created_at',
    ]
    list_filter = ['status', 'channel', 'remind_at', 'created_at']
    search_fields = [
        'dedup_key',
        'last_error',
        'user__email',
    ]
    autocomplete_fields = ['user']
    readonly_fields = ['created_at']
    date_hierarchy = 'remind_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'notification_type',
        'message',
        'is_read',
        'created_at',
    ]
    list_filter = ['is_read', 'notification_type', 'created_at']
    search_fields = [
        'message',
        'link',
        'user__email',
    ]
    autocomplete_fields = ['user']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
