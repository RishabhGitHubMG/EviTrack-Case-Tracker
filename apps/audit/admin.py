from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'user',
        'action',
        'case',
        'content_type',
        'object_id',
        'ip_address',
        'entry_hash',
    ]
    list_filter = [
        'action',
        'timestamp',
        'content_type',
    ]
    search_fields = [
        'action',
        'object_id',
        'user__email',
        'case__case_no',
        'case__title',
        'entry_hash',
        'prev_hash',
        'ip_address',
    ]
    readonly_fields = [
        'user',
        'action',
        'case',
        'content_type',
        'object_id',
        'ip_address',
        'user_agent',
        'timestamp',
        'details',
        'prev_hash',
        'entry_hash',
    ]
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
