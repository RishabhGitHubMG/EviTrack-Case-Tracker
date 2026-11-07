from django.contrib import admin, messages

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    actions = ['verify_audit_chain']
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

    def get_actions(self, request):
        return {
            'verify_audit_chain': (
                self.verify_audit_chain,
                'verify_audit_chain',
                'Verify the audit hash chain',
            ),
        }

    @admin.action(description='Verify the audit hash chain')
    def verify_audit_chain(self, request, queryset):
        result = AuditLog.verify_chain()
        if result.is_valid:
            self.message_user(
                request,
                f'Audit chain verified: {result.verified_count} entries checked.',
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                f'Audit chain verification failed: {result.error}',
                level=messages.ERROR,
            )
