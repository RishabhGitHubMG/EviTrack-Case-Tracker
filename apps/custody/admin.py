from django.contrib import admin

from apps.custody.models import CustodyEvent


@admin.register(CustodyEvent)
class CustodyEventAdmin(admin.ModelAdmin):
    list_display = [
        'evidence',
        'from_user',
        'to_user',
        'status',
        'requested_at',
        'resolved_at',
        'resolved_by',
    ]
    list_filter = ['status', 'requested_at', 'resolved_at']
    search_fields = [
        'evidence__evidence_no',
        'evidence__title',
        'reason',
        'from_user__email',
        'to_user__email',
        'resolved_by__email',
    ]
    autocomplete_fields = ['evidence', 'from_user', 'to_user', 'resolved_by']
    readonly_fields = ['requested_at']
    date_hierarchy = 'requested_at'
