import pytest
from django.urls import reverse

from apps.accounts.models import User


@pytest.mark.django_db
def test_registration_shows_field_errors_for_invalid_passwords(client):
    response = client.post(reverse('accounts:register'), {
        'first_name': 'Case',
        'last_name': 'Worker',
        'email': 'case.worker@example.test',
        'role': User.Role.INVESTIGATOR,
        'password1': 'weak',
        'password2': 'different',
    })

    assert response.status_code == 200
    assert b'Password must be at least 8 characters' in response.content

    response = client.post(reverse('accounts:register'), {
        'first_name': 'Case',
        'last_name': 'Worker',
        'email': 'case.worker@example.test',
        'role': User.Role.INVESTIGATOR,
        'password1': 'Strong#Pass123',
        'password2': 'Different#Pass123',
    })
    assert response.status_code == 200
    assert b'two password fields did not match' in response.content


@pytest.mark.django_db
def test_registration_creates_active_account_pending_approval(client):
    response = client.post(reverse('accounts:register'), {
        'first_name': 'Case',
        'last_name': 'Worker',
        'email': 'case.worker@example.test',
        'role': User.Role.INVESTIGATOR,
        'password1': 'Strong#Pass123',
        'password2': 'Strong#Pass123',
    })

    assert response.status_code == 302
    user = User.objects.get(email='case.worker@example.test')
    assert user.is_active
    assert not user.is_approved
    assert b'after an administrator approves' in client.get(reverse('accounts:register')).content
