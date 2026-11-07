"""
Security, Role-Based Access Control (RBAC), and Case Permission Mixins for EviTrack.
Designed to be reusable across all EviTrack applications (cases, evidence, custody, hearings, etc.).
"""
import logging
from typing import Any, Optional

from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)


def check_case_access(user: Any, case: Any) -> bool:
    """
    Stand-alone helper function to verify if a user has access rights to a specific case.
    Admins, Case Managers, and Superusers have global case access.
    Other users require an active CaseAssignment on that specific case.
    """
    if not user or not user.is_authenticated:
        return False

    if getattr(user, 'is_admin', False) or getattr(user, 'is_case_manager', False) or getattr(user, 'is_superuser', False):
        return True

    if case is None:
        return False

    from apps.cases.models import CaseAssignment
    return CaseAssignment.objects.filter(case=case, user=user).exists()


def get_user_accessible_cases(user: Any):
    """
    Returns a QuerySet of all Case instances the specified user is authorized to view.
    Admins, Case Managers, and Superusers can view all cases.
    Other roles are restricted to cases they are actively assigned to.
    """
    from apps.cases.models import Case
    if not user or not user.is_authenticated:
        return Case.objects.none()

    if getattr(user, 'is_admin', False) or getattr(user, 'is_case_manager', False) or getattr(user, 'is_superuser', False):
        return Case.objects.all()

    return Case.objects.filter(assignments__user=user).distinct()


class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin that restricts view access strictly to users with the Admin role or Superuser status.
    """
    permission_denied_message = "Administrative privileges are required to access this resource."

    def test_func(self) -> bool:
        user = self.request.user
        return bool(user.is_authenticated and (getattr(user, 'is_admin', False) or user.is_superuser))

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied(self.permission_denied_message)


class CaseManagerOrAdminMixin(UserPassesTestMixin):
    """
    Mixin that allows access to Case Managers and Admins.
    """
    permission_denied_message = "Case Manager or Administrator privileges are required."

    def test_func(self) -> bool:
        user = self.request.user
        return bool(
            user.is_authenticated
            and (
                getattr(user, 'is_admin', False)
                or getattr(user, 'is_case_manager', False)
                or user.is_superuser
            )
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied(self.permission_denied_message)


class ApprovedUserMixin(UserPassesTestMixin):
    """
    Ensures that the authenticated user's account has been verified and approved by an administrator.
    """
    permission_denied_message = "Your account is pending administrator approval."

    def test_func(self) -> bool:
        user = self.request.user
        return bool(user.is_authenticated and getattr(user, 'is_approved', False))

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied(self.permission_denied_message)


class ReadOnlyMixin(AccessMixin):
    """
    Enforces read-only behavior for users assigned the 'Reviewer' role.
    Reviewers are permitted to view records (GET, HEAD, OPTIONS) but cannot perform
    mutating actions (POST, PUT, PATCH, DELETE).
    """
    read_only_methods = ('GET', 'HEAD', 'OPTIONS')
    permission_denied_message = "Reviewers are granted read-only permissions and cannot modify or create records."

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if getattr(request.user, 'is_reviewer', False):
            if request.method not in self.read_only_methods:
                raise PermissionDenied(self.permission_denied_message)

        return super().dispatch(request, *args, **kwargs)


class CaseAccessMixin(AccessMixin):
    """
    Checks that the current user has access to a specific case.
    Access is granted if:
      1. User is an Admin or Superuser.
      2. User is a Case Manager.
      3. User has an active CaseAssignment on this specific case.

    Case identification strategy:
      - If view defines `get_case()`, use that.
      - If view has `case_pk` or `case_id` in kwargs, look up `Case`.
      - If view's model is `Case` and `pk` is in kwargs, look up `Case`.
      - If view has `get_object()` returning a `Case` or an object with `.case`, use that.
    """
    case_lookup_url_kwarg = 'case_pk'
    permission_denied_message = "You do not have authorization to access or modify this case."

    def get_case(self) -> Optional[object]:
        """
        Locates the Case instance associated with the current request.
        """
        from apps.cases.models import Case

        # 1. Direct instance attribute if set by parent or middleware
        if hasattr(self, 'case') and self.case:
            return self.case

        # 2. Check explicit kwargs
        case_pk = self.kwargs.get(self.case_lookup_url_kwarg) or self.kwargs.get('case_id')
        if case_pk:
            return get_object_or_404(Case, pk=case_pk)

        # 3. Check if view's model is Case and pk is in kwargs
        model = getattr(self, 'model', None)
        if model is Case and ('pk' in self.kwargs or 'id' in self.kwargs):
            pk = self.kwargs.get('pk') or self.kwargs.get('id')
            return get_object_or_404(Case, pk=pk)

        # 4. Check get_object() if available
        if hasattr(self, 'get_object') and callable(self.get_object):
            try:
                obj = self.get_object()
                if isinstance(obj, Case):
                    return obj
                if hasattr(obj, 'case') and isinstance(obj.case, Case):
                    return obj.case
            except Exception:
                pass

        return None

    def has_case_access(self, user, case) -> bool:
        """
        Determines whether the given user has access rights to the given case.
        """
        if case is None:
            return user.is_authenticated
        return check_case_access(user, case)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        case = self.get_case()
        if not self.has_case_access(request.user, case):
            logger.warning(
                "Access denied: User %s (%s) attempted to access Case %s without assignment.",
                request.user.email,
                request.user.role,
                getattr(case, 'case_no', getattr(case, 'pk', 'Unknown')),
            )
            raise PermissionDenied(self.permission_denied_message)

        # Store resolved case on self for convenience in views
        self.resolved_case = case
        return super().dispatch(request, *args, **kwargs)
