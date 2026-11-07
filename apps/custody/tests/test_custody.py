import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.cases.models import CaseAssignment
from apps.custody.models import CustodyEvent
from apps.custody.services import request_transfer
from apps.evidence.models import Evidence
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def custody_world(make_user, make_case):
    manager = make_user(role=User.Role.CASE_MANAGER)
    holder = make_user(role=User.Role.INVESTIGATOR)
    recipient = make_user(role=User.Role.CUSTODIAN)
    outsider = make_user(role=User.Role.INVESTIGATOR)
    case = make_case(owner=manager, assignees=[holder, recipient])
    evidence = Evidence.objects.create(
        case=case, title='Synthetic drive image', file_path='evidence/custody.txt',
        original_filename='custody.txt', mime_type='text/plain', file_size=4, sha256='a' * 64,
        uploaded_by=holder, current_holder=holder,
    )
    return {
        'manager': manager, 'holder': holder, 'recipient': recipient,
        'outsider': outsider, 'case': case, 'evidence': evidence,
    }


def _request(world, reason='Forensic lab examination'):
    return request_transfer(
        evidence=world['evidence'], from_user=world['holder'], to_user=world['recipient'], reason=reason,
    )


def _respond_url(event):
    return reverse('custody:custody_respond', kwargs={'pk': event.pk})


def test_request_view_creates_pending_transfer_without_moving_custody(client_for, custody_world):
    world = custody_world
    url = reverse('custody:custody_request', kwargs={'evidence_id': world['evidence'].pk})

    response = client_for(world['holder']).post(url, {
        'to_user': world['recipient'].pk, 'reason': 'Court presentation',
    })

    assert response.status_code == 302
    event = CustodyEvent.objects.get(evidence=world['evidence'])
    assert event.status == CustodyEvent.Status.REQUESTED
    assert event.to_user == world['recipient']
    world['evidence'].refresh_from_db()
    assert world['evidence'].current_holder == world['holder']
    assert Notification.objects.filter(user=world['recipient'], link=_respond_url(event)).exists()
    assert AuditLog.objects.filter(action='custody.transfer_requested').exists()


def test_request_form_excludes_current_holder_and_reviewers(client_for, custody_world, make_user):
    world = custody_world
    make_user(role=User.Role.REVIEWER)
    url = reverse('custody:custody_request', kwargs={'evidence_id': world['evidence'].pk})

    response = client_for(world['holder']).get(url)

    recipients = set(response.context['form'].fields['to_user'].queryset)
    assert world['holder'] not in recipients
    assert all(user.role != User.Role.REVIEWER for user in recipients)
    assert world['recipient'] in recipients


def test_accept_moves_custody_and_notifies_sender(client_for, custody_world):
    world = custody_world
    event = _request(world)

    response = client_for(world['recipient']).post(_respond_url(event), {'action': 'accept'})

    assert response.status_code == 302
    event.refresh_from_db()
    assert event.status == CustodyEvent.Status.ACCEPTED
    assert event.resolved_by == world['recipient']
    assert event.resolved_at is not None
    world['evidence'].refresh_from_db()
    assert world['evidence'].current_holder == world['recipient']
    sender_note = Notification.objects.get(user=world['holder'])
    assert sender_note.notification_type == Notification.NotificationType.SUCCESS
    assert AuditLog.objects.filter(action='custody.transfer_accepted').exists()


def test_reject_keeps_custody_and_logs_reason(client_for, custody_world):
    world = custody_world
    event = _request(world)

    response = client_for(world['recipient']).post(_respond_url(event), {
        'action': 'reject', 'reason': 'Seal damaged on arrival',
    })

    assert response.status_code == 302
    event.refresh_from_db()
    assert event.status == CustodyEvent.Status.REJECTED
    assert 'Seal damaged on arrival' in event.reason
    world['evidence'].refresh_from_db()
    assert world['evidence'].current_holder == world['holder']
    sender_note = Notification.objects.get(user=world['holder'])
    assert sender_note.notification_type == Notification.NotificationType.WARNING
    assert 'Seal damaged on arrival' in sender_note.message
    audit = AuditLog.objects.get(action='custody.transfer_rejected')
    assert audit.details['rejection_reason'] == 'Seal damaged on arrival'


def test_reject_without_reason_is_refused(client_for, custody_world):
    world = custody_world
    event = _request(world)

    response = client_for(world['recipient']).post(_respond_url(event), {'action': 'reject', 'reason': '  '})

    assert response.status_code == 200
    event.refresh_from_db()
    assert event.status == CustodyEvent.Status.REQUESTED
    world['evidence'].refresh_from_db()
    assert world['evidence'].current_holder == world['holder']
    assert not AuditLog.objects.filter(action='custody.transfer_rejected').exists()


@pytest.mark.parametrize('actor_key', ['outsider', 'holder'])
def test_only_recipient_or_admin_can_respond(client_for, custody_world, actor_key):
    world = custody_world
    event = _request(world)
    actor = world[actor_key]
    if actor_key == 'outsider':
        CaseAssignment.objects.filter(case=world['case'], user=actor).delete()

    response = client_for(actor).post(_respond_url(event), {'action': 'accept'})

    assert response.status_code == 403
    event.refresh_from_db()
    assert event.status == CustodyEvent.Status.REQUESTED
    world['evidence'].refresh_from_db()
    assert world['evidence'].current_holder == world['holder']


def test_admin_can_respond_on_behalf_of_recipient(client_for, custody_world, make_user):
    world = custody_world
    event = _request(world)
    admin = make_user(role=User.Role.ADMIN)

    client_for(admin).post(_respond_url(event), {'action': 'accept'})

    event.refresh_from_db()
    assert event.status == CustodyEvent.Status.ACCEPTED
    assert event.resolved_by == admin


def test_resolved_transfer_cannot_be_answered_again(client_for, custody_world):
    world = custody_world
    event = _request(world)
    client = client_for(world['recipient'])
    client.post(_respond_url(event), {'action': 'accept'})

    client.post(_respond_url(event), {'action': 'reject', 'reason': 'Changed my mind'})

    event.refresh_from_db()
    assert event.status == CustodyEvent.Status.ACCEPTED
    assert not AuditLog.objects.filter(action='custody.transfer_rejected').exists()


def test_request_page_refuses_users_without_case_access(client_for, custody_world):
    world = custody_world
    url = reverse('custody:custody_request', kwargs={'evidence_id': world['evidence'].pk})

    response = client_for(world['outsider']).get(url)

    assert response.status_code == 403


def test_timeline_partial_shows_accepted_transfer(client_for, custody_world):
    world = custody_world
    event = _request(world)
    client_for(world['recipient']).post(_respond_url(event), {'action': 'accept'})
    url = reverse('custody:custody_timeline', kwargs={'evidence_id': world['evidence'].pk})

    response = client_for(world['holder']).get(url)

    assert response.status_code == 200
    assert 'Custody Transfer' in response.content.decode()
    assert 'Accepted' in response.content.decode()


def test_qr_label_page_and_image_formats(client_for, custody_world):
    world = custody_world
    base_url = reverse('custody:custody_qr_label', kwargs={'evidence_id': world['evidence'].pk})
    client = client_for(world['holder'])

    page = client.get(base_url)
    png = client.get(base_url, {'format': 'png'})
    pdf = client.get(base_url, {'format': 'pdf'})

    assert page.status_code == 200
    assert page['Content-Type'].startswith('text/html')
    assert 'custody/qr_label.html' in [t.name for t in page.templates]
    assert png['Content-Type'] == 'image/png'
    assert png.content.startswith(b'\x89PNG')
    assert pdf['Content-Type'] == 'application/pdf'
    assert pdf.content.startswith(b'%PDF')
