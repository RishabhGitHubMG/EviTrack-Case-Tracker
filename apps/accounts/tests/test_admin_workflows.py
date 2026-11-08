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


@pytest.mark.django_db
def test_user_list_filters_status_and_changes_role(make_user, client_for):
    admin = make_user(role=User.Role.ADMIN)
    pending = make_user(approved=False)
    active = make_user()
    client = client_for(admin)

    response = client.get(reverse('accounts:user_list'), {'status': 'pending'})

    assert response.status_code == 200
    assert [user.pk for user in response.context['users']] == [pending.pk]
    assert b'name="status"' in response.content
    all_users_page = client.get(reverse('accounts:user_list'))
    assert reverse('accounts:user_role', kwargs={'pk': active.pk}).encode() in all_users_page.content

    role_url = reverse('accounts:user_role', kwargs={'pk': active.pk})
    response = client.post(role_url, {'role': User.Role.REVIEWER})

    assert response.status_code == 302
    active.refresh_from_db()
    assert active.role == User.Role.REVIEWER
