import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db


def test_admin_verify_chain_reports_success(make_user, client_for):
    AuditLog.objects.create(user=make_user(), action='security.test')
    admin = make_user(role=User.Role.ADMIN)

    response = client_for(admin).post(reverse('audit:audit_verify_chain'), follow=True)

    assert response.status_code == 200
    assert 'Audit chain verified' in response.content.decode()


def test_non_admin_cannot_verify_chain(make_user, client_for):
    investigator = make_user(role=User.Role.INVESTIGATOR)

    response = client_for(investigator).post(reverse('audit:audit_verify_chain'))

    assert response.status_code in (302, 403)
    assert 'Audit chain verified' not in response.content.decode()


def test_audit_log_page_shows_verify_chain_button(make_user, client_for):
    admin = make_user(role=User.Role.ADMIN)

    html = client_for(admin).get(reverse('audit:audit_log_list')).content.decode()

    assert reverse('audit:audit_verify_chain') in html
