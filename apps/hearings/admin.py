from django.contrib import admin

from apps.hearings.models import Hearing, Task


@admin.register(Hearing)
class HearingAdmin(admin.ModelAdmin):
    list_display = [
        'case',
        'hearing_date',
        'court',
        'purpose',
        'next_hearing_date',
        'created_by',
    ]
    list_filter = ['hearing_date', 'court']
    search_fields = [
        'court',
        'purpose',
        'outcome',
        'notes',
        'case__case_no',
        'case__title',
    ]
    autocomplete_fields = ['case', 'created_by']
    date_hierarchy = 'hearing_date'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'case',
        'assigned_to',
        'due_date',
        'status',
        'is_filing_deadline',
        'created_by',
        'created_at',
        'completed_at',
    ]
    list_filter = ['status', 'is_filing_deadline', 'due_date', 'created_at']
    search_fields = [
        'title',
        'description',
        'case__case_no',
        'case__title',
        'assigned_to__email',
    ]
    autocomplete_fields = ['case', 'assigned_to', 'created_by']
    readonly_fields = ['created_at']
    date_hierarchy = 'due_date'
