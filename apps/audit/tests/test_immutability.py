from unittest.mock import Mock, patch

import pytest
from django.contrib import admin
from django.db import DatabaseError, connection

from apps.audit.admin import AuditLogAdmin
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


def test_audit_instances_and_querysets_reject_mutation(make_user):
    entry = AuditLog.objects.create(user=make_user(), action='security.test')

    entry.action = 'security.changed'
    with pytest.raises(ValueError, match='cannot be modified'):
        entry.save()
    with pytest.raises(TypeError, match='cannot be modified'):
        AuditLog.objects.filter(pk=entry.pk).update(action='security.changed')
    with pytest.raises(TypeError, match='cannot be deleted'):
        AuditLog.objects.filter(pk=entry.pk).delete()


def test_database_triggers_reject_raw_updates_and_deletes(make_user):
    entry = AuditLog.objects.create(user=make_user(), action='security.test')

    with connection.cursor() as cursor:
        with pytest.raises(DatabaseError):
            cursor.execute('UPDATE audit_log SET action = %s WHERE id = %s', ['tampered', entry.pk])
        with pytest.raises(DatabaseError):
            cursor.execute('DELETE FROM audit_log WHERE id = %s', [entry.pk])

    entry.refresh_from_db()
    assert entry.action == 'security.test'


def test_audit_admin_disables_mutating_permissions():
    audit_admin = AuditLogAdmin(AuditLog, admin.site)
    request = Mock()

    assert not audit_admin.has_add_permission(request)
    assert not audit_admin.has_change_permission(request)
    assert not audit_admin.has_delete_permission(request)


def test_audit_admin_verify_action_reports_valid_chain(make_user):
    AuditLog.objects.create(user=make_user(), action='security.test')
    audit_admin = AuditLogAdmin(AuditLog, admin.site)
    request = Mock()

    with patch.object(audit_admin, 'message_user') as message_user:
        audit_admin.verify_audit_chain(request, AuditLog.objects.none())

    message_user.assert_called_once()
    assert '1 entries checked' in message_user.call_args.args[1]
