import pytest
from django.urls import reverse

from apps.accounts.models import User


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('action', 'next_url', 'expected_name'),
    [
        ('user_approve', '/accounts/users/', None),
        ('user_approve', '//outside.example/path', 'accounts:user_approval'),
        ('user_reject', '/accounts/users/', None),
        ('user_reject', '//outside.example/path', 'accounts:user_approval'),
    ],
)
def test_approval_actions_only_redirect_to_same_host(
    make_user, client_for, action, next_url, expected_name
):
    admin = make_user(role=User.Role.ADMIN)
    user = make_user(approved=False)
    url = reverse(f'accounts:{action}', kwargs={'pk': user.pk})

    response = client_for(admin).post(url, {'next': next_url})

    expected = reverse(expected_name) if expected_name else '/accounts/users/'
    assert response.status_code == 302
    assert response['Location'] == expected
    user.refresh_from_db()
    if action == 'user_approve':
        assert user.is_approved and user.is_active
    else:
        assert not user.is_approved and not user.is_active
