# EviTrack Progress

Status legend: **Complete** (works, tested) · **Partial** (code exists, not wired or incomplete) · **Broken** (code exists but fails at runtime) · **Missing** (not present).

## 1. Phase 0 analysis (baseline as found)

### Verification performed
- `manage.py check`: passes (URL files are placeholders, so broken views are not imported at check time).
- `makemigrations --check`: no drift. Migrations exist for accounts, cases, evidence, custody, hearings, notifications, audit. `core` and `reports` have no migrations (no models).
- Importing every views/services module: all import except `apps.reports.views` (file does not exist).
- No automated tests, no `pytest.ini`, no `seed_demo` command, no Dockerfile or docker-compose, no `docs/`.
- Not run end-to-end in a browser at baseline.

### Detected stack
Django 5.1, DRF, django-axes, argon2-cffi, Celery/Beat/Redis, qrcode, Pillow, WeasyPrint, pyotp, pytest-django.
Deviations from spec: `django-otp` not used (pyotp TOTP only, OTP is optional per user); CSP settings exist but no middleware enforces them; no `django-csp`.

### Module status (baseline)

| # | Module | Status | Notes |
|---|--------|--------|-------|
| 1 | Accounts & Access | Broken | `accounts/urls.py` is placeholder lambdas, so login, logout, profile, approval, etc. never render. No account templates except `register.html`, which uses a missing URL name. OTP is TOTP-only and optional. |
| 2 | Case Management | Broken | Views call `CaseAccessMixin.get_user_cases`, `CaseAccessMixin.user_has_case_access` and `self.check_case_access`, none of which exist. No case templates. Case Manager has global access (spec says only managed cases). Lead can close cases (spec says Case Manager/Admin only). Tab UI and timeline partial missing. |
| 3 | Evidence Vault | Broken | Same missing helpers across all views and the API. `EvidenceVerifyView` and `verify_case_evidence_task` build `Notification(recipient=, title=, level=, case=)`, which the model does not have, so tamper detection crashes. Detail view uses `item.versions`, but the relation is `newer_versions`. No evidence templates. Upload checks are partial (double-extension and MIME checks are lenient). |
| 4 | Chain of Custody | Partial | Services (`request_transfer`, `accept_transfer`, `reject_transfer`), views, forms and QR label view exist. URLs are placeholders. Four templates exist. |
| 5 | Hearings & Deadlines | Partial | Services and views exist and import. URLs are placeholders. Templates exist for hearing list/create/detail/update and task list. Missing: `task_create`, `task_update`, calendar page. `CalendarEventsAPIView` reverses `hearings:task_update`, which is not routed. |
| 6 | Reminders & Notifications | Missing | `scan_and_send_due_reminders` is a stub. No sending, retry, backoff, escalation. Notification URLs are placeholders. Context processor returns a constant 0. Topbar expects `level`, `title`, `recent_notifications`. |
| 7 | Reports & Dashboard | Missing | No reports views, models or PDF code. Core URLs are empty, so there is no dashboard or landing route. `cases:dashboard` aliases the case list. |
| 8 | Audit & Security | Partial | `AuditLog` has a SHA-256 hash chain and `verify_chain`. Immutability is ORM-only (queryset `update()` and `delete()` bypass it). No DB trigger. Viewer is a placeholder. No CSV export. Security settings page missing. No CSP middleware. No upload or auth rate limiting. |
| 9 | Global search | Missing | JS calls `/cases/api/search/`, which does not exist. |

### Data model (12 core tables)
Present: user, case, case_assignment, party, evidence, custody_event, integrity_check, hearing, task, reminder, notification, audit_log (plus `evidence_tag`).
Gaps: `Notification` has no `title`, `level` or `case`. Reminder `dedup_key` omits the fire time, so a rescheduled reminder that matches a previously sent one is never created.

### Bugs found (baseline)
1. `apps/accounts/urls.py`: placeholder lambdas for login, logout, profile, users, preferences, security.
2. `apps/accounts/mixins.py`: missing `CaseAccessMixin.get_user_cases`, `CaseAccessMixin.user_has_case_access`, instance `check_case_access`. Affects cases, evidence, evidence API.
3. `apps/evidence/views.py` `EvidenceVerifyView` and `apps/evidence/tasks.py`: `Notification` with non-existent fields (tamper path crashes).
4. `apps/evidence/views.py` `EvidenceDetailView`: `item.versions` relation does not exist.
5. Templates missing for cases, evidence, accounts (except register), core, notifications, reports, audit, calendar, task create/update.
6. `templates/base_minimal.html`: `{% url 'landing' %}` has no matching name. Any page extending it raises `NoReverseMatch`.
7. `templates/accounts/register.html`: `{% url 'accounts:register' %}` has no matching name.
8. `apps/core/views.py`: error handlers render `core/403.html` etc. The files live in `templates/errors/`, so error pages would 500.
9. `templates/partials/topbar.html` and `sidebar.html`: use `recent_notifications`, `unread_notification_count`, `notif.level`, `notif.title`; context processor provides `unread_notifications_count`.
10. `templates/base.html` JS config: session ping and theme URLs point to `/accounts/api/...`, which is not where the API is mounted (`/api/auth/...`). Notification count and search URLs do not exist.
11. Sidebar "Tasks" link points to the case list via `cases:task_list`.
12. `apps/hearings/views.py` `CalendarEventsAPIView` reverses `hearings:task_update`, which is not routed.
13. `apps/hearings/services/__init__.py`: reminder `dedup_key` omits the fire time (see data model).
14. `apps/cases/views.py` `CaseUpdateView`: Lead can change status to Closed or Archived.
15. `apps/accounts/mixins.py` `check_case_access`: Case Manager has global access, not limited to cases they manage.
16. `apps/evidence/forms.py`: MIME check passes when the declared type is `application/octet-stream` and the guessed type is not allowlisted. Double-extension check only looks at dangerous intermediate parts.
17. `apps/reports/`: no views file, no models, no services.
18. `apps/core/urls.py`: empty, so `/` and `/dashboard/` do not resolve.

### Security gaps (baseline)
- Audit immutability only at ORM level (no DB trigger).
- No CSP or HSTS enforcement beyond production setting values (no middleware).
- No rate limiting on login (axes lockout only), OTP, or upload endpoints.
- Evidence served only via `FileResponse`. No X-Accel-Redirect path for production.
- Several views would raise `AttributeError` (500) rather than deny, so access control is not exercised.

## 2. Decisions

- Keep the existing Django, DRF, pyotp and axes stack. Do not add `django-otp`; email OTP is implemented on top of pyotp and Django email.
- Every login requires a 6-digit email OTP (console email backend in development). Users who enable an authenticator app (TOTP) use that instead.
- `Notification` keeps its current fields. Callers are updated to `create_notification(user, message, link, notification_type)`.
- Case Manager sees cases they created or are assigned to. Admin sees all. Other roles see assigned cases only.
- Only Case Manager or Admin can close or archive a case, and only they can assign users or receive integrity alerts.
- Tamper detection notifies the Case Manager(s) of the case, in-app and by email.
- Reminders run from Celery Beat every 5 minutes (existing schedule). Failed sends retry with exponential backoff (max 3 attempts), then escalate to the Case Manager.
- Evidence downloads use `FileResponse` in development and X-Accel-Redirect when `EVIDENCE_USE_X_ACCEL` is enabled.
- Audit immutability is enforced in three layers: model `save`/`delete`, Django admin (read-only), and a DB trigger (PostgreSQL and SQLite).

## 3. Checklist (live)

Each row is updated as work is completed. Final state must be **Complete** for every row.

| Area | Item | Status |
|------|------|--------|
| Foundation | pytest config, test settings, shared fixtures | Missing |
| Foundation | Accounts URL routing | Broken |
| Foundation | Case access helpers and Case Manager scope | Broken |
| 1 Accounts | Register, approval queue, approve/reject, role change | Broken |
| 1 Accounts | Login with email OTP (every login), TOTP option, profile, password change | Broken |
| 1 Accounts | Session timeout (15 min, warning modal), lockout, failed-login view | Partial |
| 2 Cases | List, filter, sort, create, detail tabs, edit, transitions, assign, parties, timeline | Broken |
| 3 Evidence | Upload (drag-drop, progress), versions, preview, download log, verify, bulk verify, metadata, QR | Broken |
| 4 Custody | Request, accept/reject, timeline, QR label, pending on dashboard | Partial |
| 5 Hearings | Calendar, hearings CRUD, outcome and next date, tasks CRUD, overdue | Partial |
| 6 Notifications | Scheduling, email/SMS/in-app delivery, retry, escalation, idempotent, bell, notification page | Missing |
| 7 Reports | Dashboard KPIs and charts, PDF exports (5), audit logging | Missing |
| 8 Audit | Viewer with filters, CSV export, failed logins, integrity history, security settings, insert-only trigger | Partial |
| 9 Search | Global search API and dropdown | Missing |
| UI | Design tokens, dark mode, responsive shell, landing, error pages, login/OTP pages | Partial |
| Security | CSRF, secure cookies, CSP, HSTS, rate limiting, input validation | Partial |
| Data | `seed_demo` (roles, cases, evidence incl. one tampered file, custody, hearings, tasks) | Missing |
| Tests | Hashing, versioning, tamper, custody, IDOR, audit immutability, uploads, reminders, status transitions, OTP/lockout | Missing |
| Deploy | Dockerfile, docker-compose (web, nginx, postgres, redis, celery worker, beat), `.env.example` | Missing |
| Docs | README (setup, env, Celery, seed, 5-minute demo, structure) | Partial |
| QA | `manage.py check --deploy`, full test run, responsive check mobile/tablet/desktop | Missing |
