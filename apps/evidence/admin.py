from django.contrib import admin

from apps.evidence.models import Evidence, IntegrityCheck, Tag


class IntegrityCheckInline(admin.TabularInline):
    model = IntegrityCheck
    extra = 0
    readonly_fields = [
        'checked_by',
        'result',
        'computed_hash',
        'stored_hash',
        'checked_on',
    ]
    can_delete = False


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = [
        'evidence_no',
        'title',
        'case',
        'status',
        'version',
        'is_latest_version',
        'current_holder',
        'uploaded_by',
        'uploaded_at',
    ]
    list_filter = [
        'status',
        'is_latest_version',
        'uploaded_at',
        'mime_type',
    ]
    search_fields = [
        'evidence_no',
        'title',
        'original_filename',
        'sha256',
        'case__case_no',
        'case__title',
    ]
    readonly_fields = [
        'evidence_no',
        'uploaded_at',
        'sha256',
        'file_size',
        'mime_type',
    ]
    filter_horizontal = ['tags']
    inlines = [IntegrityCheckInline]
    autocomplete_fields = ['case', 'uploaded_by', 'current_holder', 'parent']


@admin.register(IntegrityCheck)
class IntegrityCheckAdmin(admin.ModelAdmin):
    list_display = [
        'evidence',
        'result',
        'checked_by',
        'checked_on',
        'computed_hash',
        'stored_hash',
    ]
    list_filter = ['result', 'checked_on']
    search_fields = [
        'evidence__evidence_no',
        'evidence__title',
        'computed_hash',
        'stored_hash',
        'checked_by__email',
    ]
    readonly_fields = [
        'evidence',
        'checked_by',
        'result',
        'computed_hash',
        'stored_hash',
        'checked_on',
    ]
    autocomplete_fields = ['evidence', 'checked_by']
