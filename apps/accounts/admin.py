from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = [
        'email',
        'first_name',
        'last_name',
        'role',
        'is_approved',
        'is_active',
        'is_staff',
        'otp_enabled',
    ]
    list_filter = [
        'role',
        'is_approved',
        'is_active',
        'is_staff',
        'is_superuser',
        'otp_enabled',
        'dark_mode',
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone')}),
        (
            'Role & Permissions',
            {
                'fields': (
                    'role',
                    'is_approved',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        (
            'Security & Two-Factor Authentication',
            {'fields': ('otp_secret', 'otp_enabled')},
        ),
        (
            'Preferences',
            {
                'fields': (
                    'dark_mode',
                    'notify_email',
                    'notify_sms',
                    'notify_inapp',
                    'hearing_reminder_minutes',
                    'deadline_reminder_minutes',
                )
            },
        ),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'role',
                    'is_approved',
                    'password1',
                    'password2',
                ),
            },
        ),
    )
