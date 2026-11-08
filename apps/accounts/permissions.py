"""
Capability matrix from docs/SPEC.md section 1. Scope rules (own/assigned cases) are enforced
per object by apps/core/api/permissions.py, not by these strings.
"""
from apps.accounts.models import User

ADMIN = User.Role.ADMIN
MANAGER = User.Role.CASE_MANAGER
INVESTIGATOR = User.Role.INVESTIGATOR
CUSTODIAN = User.Role.CUSTODIAN
REVIEWER = User.Role.REVIEWER
ALL_ROLES = frozenset(User.Role.values)

CAPABILITY_ROLES = {
    'cases.view': ALL_ROLES,
    'cases.create': frozenset({ADMIN, MANAGER}),
    'cases.edit': frozenset({ADMIN, MANAGER, INVESTIGATOR}),
    'cases.assign': frozenset({ADMIN, MANAGER}),
    'cases.close': frozenset({ADMIN, MANAGER}),
    'evidence.view': ALL_ROLES,
    'evidence.upload': frozenset({ADMIN, MANAGER, INVESTIGATOR, CUSTODIAN}),
    'evidence.verify': frozenset({ADMIN, MANAGER, INVESTIGATOR, CUSTODIAN}),
    'evidence.integrity.view': ALL_ROLES,
    'custody.transfer': frozenset({ADMIN, MANAGER, INVESTIGATOR, CUSTODIAN}),
    'hearings.manage': frozenset({ADMIN, MANAGER, INVESTIGATOR}),
    'tasks.manage': frozenset({ADMIN, MANAGER, INVESTIGATOR}),
    'reports.view': ALL_ROLES,
    'audit.view': frozenset({ADMIN, MANAGER}),
    'admin.manage': frozenset({ADMIN}),
}


def role_for(user) -> str:
    return ADMIN if user.is_superuser else user.role


def permissions_for(user) -> list[str]:
    role = role_for(user)
    return sorted(capability for capability, roles in CAPABILITY_ROLES.items() if role in roles)
