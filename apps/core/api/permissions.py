from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.mixins import check_case_access
from apps.cases.models import Case, CaseAssignment


class IsApprovedUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_approved))


class HasRole(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role in self.allowed_roles)
        )


class CaseObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        case = obj if isinstance(obj, Case) else getattr(obj, 'case', None)
        if case is None:
            return False
        user = request.user
        if not check_case_access(user, case):
            return False

        level = getattr(view, 'case_permission_level', 'view')
        if request.method in SAFE_METHODS:
            return True
        if level == 'manage':
            return bool(user.is_superuser or user.is_admin or user.is_case_manager)
        if level == 'edit':
            return bool(
                user.is_superuser
                or user.is_admin
                or user.is_case_manager
                or (
                    user.is_investigator
                    and CaseAssignment.objects.filter(case=case, user=user).exists()
                )
            )
        return False
