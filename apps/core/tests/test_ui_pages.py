from pathlib import Path

import pytest
from django.contrib.auth.hashers import check_password
from django.template.loader import render_to_string

from apps.accounts.models import User

pytestmark = pytest.mark.django_db

CSS_PATH = Path(__file__).resolve().parents[3] / 'static' / 'css' / 'evitrack.css'


def test_dark_mode_is_saved_per_user(make_user, client_for):
    first = make_user(role=User.Role.INVESTIGATOR)
    second = make_user(role=User.Role.INVESTIGATOR)

    client_for(first).post('/api/auth/preferences/theme/', {'theme': 'dark'}, content_type='application/json')

    first.refresh_from_db()
    second.refresh_from_db()
    assert first.dark_mode is True
    assert second.dark_mode is False
    assert 'data-theme="dark"' in client_for(first).get('/dashboard/').content.decode()
    assert 'data-theme="light"' in client_for(second).get('/dashboard/').content.decode()


def test_dashboard_renders_session_timeout_modal(make_user, client_for):
    html = client_for(make_user()).get('/dashboard/').content.decode()

    assert 'id="sessionTimeoutModal"' in html
    assert 'id="sessionCountdown"' in html


def test_session_expires_after_fifteen_minutes_of_inactivity(make_user, client_for):
    import time

    client = client_for(make_user())
    assert client.get('/dashboard/').status_code == 200

    session = client.session
    session['last_activity'] = time.time() - 901
    session.save()

    response = client.get('/dashboard/')
    assert response.status_code == 302
    assert '/accounts/login/' in response['Location']


def test_error_pages_have_no_javascript_urls():
    for template in ('errors/403.html', 'errors/404.html', 'errors/500.html'):
        html = render_to_string(template)
        assert 'javascript:' not in html, template


def test_not_found_page_is_branded(client):
    response = client.get('/this-route-does-not-exist/')

    assert response.status_code == 404
    assert 'Go Back' in response.content.decode()


def test_print_stylesheet_hides_app_chrome():
    css = CSS_PATH.read_text(encoding='utf-8')

    assert '@media print' in css
    assert '.app-sidebar' in css.split('@media print', 1)[1]


def test_stylesheet_defines_keyboard_focus_ring():
    assert ':focus-visible' in CSS_PATH.read_text(encoding='utf-8')


def test_password_change_rejects_weak_password(make_user, client_for):
    user = make_user(password='Sample#Pass1')
    client = client_for(user)

    response = client.post('/accounts/password/', {
        'old_password': 'Sample#Pass1',
        'new_password1': 'short',
        'new_password2': 'short',
    })

    assert response.status_code == 200
    assert response.context['form'].errors.get('new_password1')
    user.refresh_from_db()
    assert check_password('Sample#Pass1', user.password)


def test_profile_page_renders_for_authenticated_user(make_user, client_for):
    response = client_for(make_user()).get('/accounts/profile/')

    assert response.status_code == 200
    assert 'name="first_name"' in response.content.decode()
