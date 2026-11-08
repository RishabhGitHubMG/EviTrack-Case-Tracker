import pytest
from django.urls import reverse

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_admin_sees_security_policy_values(make_user, client_for, settings):
    admin = make_user(role=User.Role.ADMIN)

    response = client_for(admin).get(reverse('accounts:security_settings'))

    html = response.content.decode()
    assert response.status_code == 200
    assert f'{settings.SESSION_TIMEOUT_SECONDS // 60} minutes' in html
    assert f'{settings.EMAIL_OTP_TTL_MINUTES} minutes' in html


def test_non_admin_cannot_open_security_policy(make_user, client_for):
    investigator = make_user(role=User.Role.INVESTIGATOR)

    response = client_for(investigator).get(reverse('accounts:security_settings'))

    assert response.status_code in (302, 403)


def test_admin_sidebar_links_to_approvals_and_failed_logins(make_user, client_for):
    html = client_for(make_user(role=User.Role.ADMIN)).get('/dashboard/').content.decode()

    assert reverse('accounts:user_approval') in html
    assert reverse('accounts:failed_logins') in html


def test_non_admin_sidebar_hides_admin_links(make_user, client_for):
    html = client_for(make_user(role=User.Role.INVESTIGATOR)).get('/dashboard/').content.decode()

    assert reverse('accounts:user_approval') not in html
    assert reverse('accounts:failed_logins') not in html
