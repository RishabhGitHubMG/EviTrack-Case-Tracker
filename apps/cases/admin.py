from django.contrib import admin

from apps.cases.models import Case, CaseAssignment, Party


class CaseAssignmentInline(admin.TabularInline):
    model = CaseAssignment
    extra = 1
    autocomplete_fields = ['user']


class PartyInline(admin.StackedInline):
    model = Party
    extra = 0


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = [
        'case_no',
        'title',
        'case_type',
        'status',
        'priority',
        'opened_on',
        'closed_on',
        'created_by',
    ]
    list_filter = ['status', 'priority', 'case_type', 'opened_on']
    search_fields = ['case_no', 'title', 'description']
    readonly_fields = ['case_no', 'opened_on']
    inlines = [CaseAssignmentInline, PartyInline]
    date_hierarchy = 'opened_on'


@admin.register(CaseAssignment)
class CaseAssignmentAdmin(admin.ModelAdmin):
    list_display = ['case', 'user', 'role_on_case', 'assigned_on']
    list_filter = ['role_on_case', 'assigned_on']
    search_fields = [
        'case__case_no',
        'case__title',
        'user__email',
        'user__first_name',
        'user__last_name',
    ]
    autocomplete_fields = ['case', 'user']


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ['name', 'case', 'party_type', 'email', 'phone']
    list_filter = ['party_type']
    search_fields = [
        'name',
        'email',
        'phone',
        'case__case_no',
        'case__title',
    ]
    autocomplete_fields = ['case']
