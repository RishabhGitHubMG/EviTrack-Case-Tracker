import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['accounts:login', 'accounts:register'])
def test_public_account_pages_render(name):
    response = Client().get(reverse(name))

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['cases:case_list', 'core:dashboard', 'accounts:profile'])
def test_protected_pages_redirect_anonymous_users_to_login(name):
    response = Client().get(reverse(name))

    assert response.status_code == 302
    assert reverse('accounts:login') in response['Location']


@pytest.mark.django_db
@pytest.mark.parametrize('name', [
    'accounts:profile', 'accounts:password_change', 'accounts:otp_setup', 'accounts:user_list',
    'accounts:user_approval', 'accounts:failed_logins',
])
def test_account_pages_render_for_admin(make_user, client_for, name):
    admin = make_user(role=User.Role.ADMIN)

    response = client_for(admin).get(reverse(name))

    assert response.status_code == 200
