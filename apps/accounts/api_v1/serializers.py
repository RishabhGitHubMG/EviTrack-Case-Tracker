from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.permissions import permissions_for, role_for
from apps.custody.models import CustodyEvent
from apps.notifications.models import Notification


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=300)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    requested_role = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    remember_me = serializers.BooleanField(default=False)


class OTPCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=12)

    def validate_code(self, value):
        digits = value.replace(' ', '').replace('-', '')
        if len(digits) != 6 or not digits.isdigit():
            raise serializers.ValidationError('Enter the 6-digit code.')
        return digits


def unread_notification_count(user: User) -> int:
    return Notification.objects.filter(user=user, is_read=False).count()


def pending_custody_count(user: User) -> int:
    return CustodyEvent.objects.filter(to_user=user, status=CustodyEvent.Status.REQUESTED).count()


def pending_approval_count() -> int:
    return User.objects.filter(is_approved=False, is_active=True).count()


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    totp_enabled = serializers.BooleanField(source='otp_enabled', read_only=True)
    permissions = serializers.SerializerMethodField()
    preferences = serializers.SerializerMethodField()
    unread_notifications = serializers.SerializerMethodField()
    pending_custody = serializers.SerializerMethodField()
    pending_approvals = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'phone', 'role', 'permissions', 'preferences',
                  'totp_enabled', 'last_login', 'unread_notifications', 'pending_custody',
                  'pending_approvals')

    def get_name(self, user):
        return user.get_full_name().strip() or user.email

    def get_permissions(self, user):
        return permissions_for(user)

    def get_preferences(self, user):
        return {
            'theme': 'dark' if user.dark_mode else 'light',
            'email_enabled': user.notify_email,
            'sms_enabled': user.notify_sms,
            'reminder_hearing': user.hearing_reminder_minutes,
            'reminder_deadline': user.deadline_reminder_minutes,
        }

    def get_unread_notifications(self, user):
        return unread_notification_count(user)

    def get_pending_custody(self, user):
        return pending_custody_count(user)

    def get_pending_approvals(self, user):
        if role_for(user) != User.Role.ADMIN:
            return None
        return pending_approval_count()
