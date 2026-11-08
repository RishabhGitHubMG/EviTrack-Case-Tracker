import pytest
from django.urls import reverse

from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def inbox(make_user):
    owner = make_user()
    other = make_user()
    own_unread = Notification.objects.create(
        user=owner, message='Own unread', link='/cases/', notification_type=Notification.NotificationType.WARNING
    )
    own_read = Notification.objects.create(
        user=owner, message='Own read', is_read=True, notification_type=Notification.NotificationType.SUCCESS
    )
    foreign = Notification.objects.create(user=other, message='Foreign unread')
    return {'owner': owner, 'other': other, 'own_unread': own_unread, 'own_read': own_read, 'foreign': foreign}


def test_unread_count_endpoint_counts_only_own_unread(client_for, inbox):
    response = client_for(inbox['owner']).get(reverse('notifications_api:unread_count'))

    assert response.status_code == 200
    assert response.json() == {'unread_count': 1}


def test_unread_count_endpoint_requires_login(client):
    response = client.get(reverse('notifications_api:unread_count'))

    assert response.status_code == 302


def test_list_page_renders_only_own_notifications(client_for, inbox):
    response = client_for(inbox['owner']).get(reverse('notifications:notification_list'))

    assert response.status_code == 200
    assert 'notifications/notification_list.html' in [t.name for t in response.templates]
    messages = [n.message for n in response.context['notifications']]
    assert 'Own unread' in messages and 'Own read' in messages
    assert 'Foreign unread' not in messages


def test_unread_filter_hides_read_items(client_for, inbox):
    response = client_for(inbox['owner']).get(reverse('notifications:notification_list'), {'read': 'unread'})

    messages = [n.message for n in response.context['notifications']]
    assert messages == ['Own unread']


def test_read_filter_shows_only_read_items(client_for, inbox):
    response = client_for(inbox['owner']).get(reverse('notifications:notification_list'), {'read': 'read'})

    assert [notification.message for notification in response.context['notifications']] == ['Own read']


def test_type_filter_shows_only_own_matching_notifications(client_for, inbox):
    response = client_for(inbox['owner']).get(reverse('notifications:notification_list'), {'type': 'warning'})

    assert [notification.message for notification in response.context['notifications']] == ['Own unread']
    assert response.context['type_filter'] == 'warning'


def test_read_and_type_filters_can_be_combined(client_for, inbox):
    response = client_for(inbox['owner']).get(
        reverse('notifications:notification_list'), {'read': 'read', 'type': 'success'}
    )

    assert [notification.message for notification in response.context['notifications']] == ['Own read']


def test_invalid_notification_filters_fall_back_to_all(client_for, inbox):
    response = client_for(inbox['owner']).get(
        reverse('notifications:notification_list'), {'read': 'unknown', 'type': 'unknown'}
    )

    assert {notification.message for notification in response.context['notifications']} == {'Own unread', 'Own read'}
    assert response.context['read_filter'] == 'all'
    assert response.context['type_filter'] == ''


def test_bell_context_exposes_count_and_recent_items(client_for, inbox):
    response = client_for(inbox['owner']).get(reverse('notifications:notification_list'))

    assert response.context['unread_notification_count'] == 1
    assert {n.message for n in response.context['recent_notifications']} == {'Own unread', 'Own read'}


def test_open_marks_read_and_redirects_to_link(client_for, inbox):
    response = client_for(inbox['owner']).get(
        reverse('notifications:notification_detail', kwargs={'pk': inbox['own_unread'].pk})
    )

    assert response.status_code == 302
    assert response['Location'] == '/cases/'
    inbox['own_unread'].refresh_from_db()
    assert inbox['own_unread'].is_read is True


def test_open_external_link_falls_back_to_list(client_for, make_user):
    owner = make_user()
    note = Notification.objects.create(user=owner, message='External', link='https://evil.example/phish')

    response = client_for(owner).get(reverse('notifications:notification_detail', kwargs={'pk': note.pk}))

    assert response['Location'] == reverse('notifications:notification_list')


def test_mark_read_post_marks_single_item(client_for, inbox):
    url = reverse('notifications:notification_mark_read', kwargs={'pk': inbox['own_unread'].pk})

    response = client_for(inbox['owner']).post(url)

    assert response.status_code == 302
    inbox['own_unread'].refresh_from_db()
    assert inbox['own_unread'].is_read is True


def test_mark_read_rejects_get(client_for, inbox):
    url = reverse('notifications:notification_mark_read', kwargs={'pk': inbox['own_unread'].pk})

    response = client_for(inbox['owner']).get(url)

    assert response.status_code == 405
    inbox['own_unread'].refresh_from_db()
    assert inbox['own_unread'].is_read is False


def test_cannot_open_or_mark_another_users_notification(client_for, inbox):
    client = client_for(inbox['owner'])
    detail = reverse('notifications:notification_detail', kwargs={'pk': inbox['foreign'].pk})
    mark = reverse('notifications:notification_mark_read', kwargs={'pk': inbox['foreign'].pk})

    assert client.get(detail).status_code == 404
    assert client.post(mark).status_code == 404
    inbox['foreign'].refresh_from_db()
    assert inbox['foreign'].is_read is False


def test_mark_all_read_only_touches_own_items(client_for, inbox):
    response = client_for(inbox['owner']).post(reverse('notifications:notification_mark_all_read'))

    assert response.status_code == 302
    assert not Notification.objects.filter(user=inbox['owner'], is_read=False).exists()
    inbox['foreign'].refresh_from_db()
    assert inbox['foreign'].is_read is False
