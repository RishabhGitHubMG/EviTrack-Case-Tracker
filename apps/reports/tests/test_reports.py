import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.cases.models import CaseAssignment

pytestmark = pytest.mark.django_db

REPORT_URLS = [
    'reports:case_summary',
    'reports:evidence_register',
    'reports:custody_history',
    'reports:hearing_schedule',
    'reports:integrity_report',
]


def test_report_list_only_shows_accessible_cases(client_for, make_user, make_case):
    user = make_user()
    visible = make_case(assignees=[user], title='Visible report case')
    hidden = make_case(title='Hidden report case')

    response = client_for(user).get(reverse('reports:report_list'))

    assert response.status_code == 200
    assert visible in response.context['cases']
    assert hidden not in response.context['cases']
    assert b'Choose a case' in response.content
    for route_name in REPORT_URLS:
        assert reverse(route_name, kwargs={'case_id': visible.pk}).encode() in response.content
    assert reverse('reports:case_summary', kwargs={'case_id': hidden.pk}).encode() not in response.content


@pytest.mark.django_db
def test_report_case_picker_filters_to_accessible_selection(client_for, make_user, make_case):
    user = make_user()
    visible = make_case(assignees=[user], title='Visible report case')
    hidden = make_case(title='Hidden report case')
    client = client_for(user)

    response = client.get(reverse('reports:report_list'), {'case': str(visible.pk)})

    assert response.status_code == 200
    assert list(response.context['cases']) == [visible]
    assert response.context['selected_case'] == visible.pk
    assert f'value="{visible.pk}" selected'.encode() in response.content

    response = client.get(reverse('reports:report_list'), {'case': str(hidden.pk)})
    assert response.status_code == 200
    assert list(response.context['cases']) == []
    assert hidden.title.encode() not in response.content


@pytest.mark.parametrize('route_name', REPORT_URLS)
def test_case_reports_generate_pdf_and_write_audit_log(client_for, make_user, make_case, route_name):
    user = make_user()
    case = make_case(assignees=[user])

    response = client_for(user).get(reverse(route_name, kwargs={'case_id': case.pk}))

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response['Content-Disposition'].endswith('.pdf"')
    assert response.content.startswith(b'%PDF-')
    report_name = route_name.rsplit(':', 1)[-1]
    assert AuditLog.objects.filter(
        user=user, case=case, action=f'report.{report_name}.generated'
    ).exists()


@pytest.mark.parametrize('route_name', REPORT_URLS)
def test_case_reports_hide_inaccessible_cases(client_for, make_user, make_case, route_name):
    user = make_user()
    hidden_case = make_case()

    response = client_for(user).get(reverse(route_name, kwargs={'case_id': hidden_case.pk}))

    assert response.status_code == 404
    assert not AuditLog.objects.filter(user=user, case=hidden_case, action__startswith='report.').exists()


def test_report_list_requires_login(client):
    assert client.get(reverse('reports:report_list')).status_code == 302


def test_audit_viewer_filters_and_exports_csv(client_for, make_user, make_case):
    admin = make_user(role=User.Role.ADMIN)
    actor = make_user()
    case = make_case(assignees=[actor])
    other_case = make_case()
    matching = AuditLog.objects.create(
        user=actor, action='evidence.upload', case=case, details={'filename': 'one.pdf'}
    )
    AuditLog.objects.create(user=actor, action='case.updated', case=case)
    AuditLog.objects.create(user=admin, action='evidence.upload', case=other_case)
    query = {
        'user': str(actor.pk),
        'action': 'evidence',
        'case': str(case.pk),
        'date_from': matching.timestamp.date().isoformat(),
        'date_to': matching.timestamp.date().isoformat(),
    }

    response = client_for(admin).get(reverse('audit:audit_log_list'), query)

    assert response.status_code == 200
    assert list(response.context['audit_entries']) == [matching]

    csv_response = client_for(admin).get(reverse('audit:audit_log_export'), query)
    assert csv_response.status_code == 200
    assert csv_response['Content-Type'].startswith('text/csv')
    assert b'evidence.upload' in csv_response.content
    assert b'case.updated' not in csv_response.content


def test_my_activity_only_contains_current_users_case_accessible_entries(client_for, make_user, make_case):
    user = make_user()
    other = make_user()
    visible_case = make_case(assignees=[user])
    hidden_case = make_case()
    visible = AuditLog.objects.create(user=user, action='case.view', case=visible_case)
    AuditLog.objects.create(user=user, action='case.hidden', case=hidden_case)
    AuditLog.objects.create(user=other, action='case.other', case=visible_case)

    response = client_for(user).get(reverse('audit:my_activity'))

    assert response.status_code == 200
    assert list(response.context['audit_entries']) == [visible]


def test_audit_viewer_and_export_require_admin(client_for, make_user):
    user = make_user()

    assert client_for(user).get(reverse('audit:audit_log_list')).status_code == 403
    assert client_for(user).get(reverse('audit:audit_log_export')).status_code == 403


def test_my_activity_requires_login(client):
    assert client.get(reverse('audit:my_activity')).status_code == 302
