# EviTrack Progress

Status legend: **Complete** (works, tested) · **Partial** (code exists, not wired or incomplete) · **Broken** (code exists but fails at runtime) · **Missing** (not present).

## 0. RULES FOR THE AI (read first, every session)
1. Read this file at session start. Do not re-scan the whole repo.
2. Go to **NEXT ACTION** in the status header, do it, then continue down the checklist in section 3.
3. Update this file after every small unit of work (one feature, one fix, one test file). Change the status, rewrite NEXT ACTION, add one line to the Session Log.
4. Commit and push after every update to the working branch (never `main`). Push only when the user has authorized it for this project.
5. Keep chat replies to 1-3 lines. No code or log dumps in chat.
6. Keep what works. No rewrites, no deleting working code or migrations. Add new migrations, do not edit applied ones.
7. Never mark an item Complete unless it was run and worked.
8. Do not ask the user questions. Decide, record the decision in section 2, continue.

## STATUS HEADER (keep current)
- ANALYSIS DONE: YES (section 1 kept as written; accounts and case-access items re-verified in session 2)
- Last updated: session 11
- Session number: 11
- Overall completion: not measured (see checklist, section 3)
- **NEXT ACTION:** Step 2 (UI leftovers, continued): browser-verify dark-mode persistence per user, the session-timeout warning modal, and profile/change-password flows; run responsive checks on dashboard, case list, case detail and evidence detail (mobile sidebar drawer, table scrolling); check loading/empty/error states and focus/contrast. Print CSS, branded 403/404/500 and the dark-mode save endpoint exist in code (session 11 fixed `javascript:` links in error pages). Then Docker/evidence X-Accel setup, `.env.example`, README/demo/future-scope docs, and final status reconciliation/QA.

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
| 6 | Reminders & Notifications | Partial | Celery Beat scanner sends due email/in-app/mock-SMS reminders, persists idempotent delivery state, retries with exponential backoff (3 attempts), and escalates delivery failures and overdue tasks to case managers. Schedule defaults and notification UI exist. Email tamper alerts and a live Celery/Redis run remain unverified. |
| 7 | Reports & Dashboard | Partial | Dashboard KPIs/charts exist. Five case-scoped WeasyPrint PDFs now include generated-by/date footers and audit events; report permission and PDF tests pass. Authenticated pages not browser-tested. |
| 8 | Audit & Security | Partial | Admin viewer/CSV and hash-chain verify action are implemented and tested. ORM/queryset/admin protections plus SQLite and PostgreSQL append-only triggers are implemented; SQLite raw-write tests pass, PostgreSQL not live-tested. CSP, production HSTS, auth/upload rate limits and `check --deploy` are implemented/tested. |
| 9 | Global search | Partial | `/api/search/` returns grouped case, party and evidence results (case-scoped by the shared permission queryset; evidence search includes number, title, tags and SHA-256). Tests confirm no inaccessible-case results. Header input is wired to the API and the `/` shortcut is present, but authenticated browser interaction remains unverified. |

### Data model (12 core tables)
Present: user, case, case_assignment, party, evidence, custody_event, integrity_check, hearing, task, reminder, notification, audit_log (plus `evidence_tag`).
Gaps: `Notification` has no `title`, `level` or `case`; callers must use the notification service. Reminder deduplication now includes the fire time, so rescheduled reminders can be queued independently.

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
- Every login requires a 6-digit email OTP (console email backend in development). Users who enable TOTP verify both email OTP and authenticator code; TOTP remains optional.
- `Notification` keeps its current fields. Callers are updated to `create_notification(user, message, link, notification_type)`.
- Case Manager sees cases they created or are assigned to. Admin sees all. Other roles see assigned cases only.
- Only Case Manager or Admin can close or archive a case, and only they can assign users or receive integrity alerts.
- Tamper detection notifies the Case Manager(s) of the case, in-app and by email.
- Reminders run from Celery Beat every 5 minutes (existing schedule). Failed sends retry with exponential backoff (max 3 attempts), then escalate to the Case Manager.
- Evidence downloads use `FileResponse` in development and X-Accel-Redirect when `EVIDENCE_USE_X_ACCEL` is enabled.
- Audit immutability is enforced in three layers: model `save`/`delete`, Django admin (read-only), and a DB trigger (PostgreSQL and SQLite).

- Case-access call sites use the module functions in `apps/accounts/mixins.py` (`check_case_access`, `require_case_access`, `get_user_accessible_cases`). No static shim methods were added to `CaseAccessMixin`.
- Error pages and landing link to `core:dashboard` and `core:landing`, not `cases:dashboard`.
- `templates/base.html` and `static/css/evitrack.css` already had the design tokens, dark mode and shared components; session 3 reused them and added partials (`form_field`, `status_pill`, `empty_state`) plus `auth_base.html`.
- Case create and edit share `cases/case_form.html` through template blocks.

- Branch: work continues on the existing `ai_main_6c48a31b77464f868b18` branch. At session 6 start it matched `main` at `af2fa64`.
- Session 11 branch: `ai_main_f3020ee7e5464f779c07` at `main` commit `5e4930a` (PR #5 merged). Pushes to this branch are authorized by the project owner after each PROGRESS.md update.
- Email OTP is required after every password login; users with TOTP enabled complete an additional authenticator step. Both flows and email-code lockout are tested; browser login remains unverified.
- Custody QR label is `custody/qr_label.html` (HTML page). `?format=png` or `?format=pdf` returns the image. It includes custodian and intake date, so it stays separate from the evidence-vault label at `evidence:evidence_qr`.
- Tamper alerts (single verify and bulk task) go to the case's Case Managers (creator or assigned) via `notify_case_managers`, falling back to admins. Email delivery remains outstanding.
- Crawl test fails on placeholder, plain-text or non-template 200 responses. `KNOWN_PLACEHOLDERS` is now empty; new routes must render real responses.
- `seed_demo` is idempotent: it exits if the demo manager exists. Re-seed on a fresh database. Demo sign-in uses the emailed OTP (visible in the development console); TOTP-enabled users also enter their authenticator code.

## 3. Checklist (live)

Each row is updated as work is completed. Final state must be **Complete** for every row.

| Area | Item | Status |
|------|------|--------|
| Foundation | pytest config, test settings, shared fixtures | Partial |
| Foundation | Accounts URL routing | Partial |
| Foundation | Case access helpers and Case Manager scope | Complete |
| Foundation | Data model: 12 tables with indexes and constraints | Partial |
| Foundation | Services layer (hashing, custody, reminders) and thin views | Partial |
| Foundation | Evidence storage outside web root, served via authenticated audit-logged view | Partial |
| Audit | Hash chain with verify action and database immutability | Partial (admin verify action, ORM/queryset protection and SQLite triggers tested; PostgreSQL trigger not live-tested) |
| UI | Print styles | Partial (`@media print` block in evitrack.css hides chrome and cards; not printed in a browser; no report/case print header) |
| 1 Accounts | Register, approval queue, approve/reject, role change | Partial |
| 1 Accounts | Login with email OTP (every login), TOTP option, profile, password change | Complete for OTP flow (email plus optional additional TOTP and lockout tests pass; browser not tested); profile/password flows remain partial |
| 1 Accounts | Session timeout (15 min, warning modal), lockout, failed-login view | Partial |
| 2 Cases | List, filter, sort, create, detail tabs, edit, transitions, assign, parties, timeline (full page and AJAX partial) | Partial |
| 3 Evidence | Upload (drag-drop, progress), versions, preview, download log, verify, bulk verify, metadata, QR | Partial |
| 4 Custody | Request, accept/reject, timeline, QR label, pending on dashboard | Complete (12 pytest; not clicked in browser) |
| 5 Hearings | Calendar (FullCalendar page), hearings CRUD, outcome and next date, tasks CRUD (create/update templates), overdue | Partial |
| 6 Notifications | Scheduling, email/SMS/in-app delivery, retry, escalation, idempotent, bell, notification page | Partial (default schedule, email/in-app/mock-SMS delivery, deduplication, retry/backoff, failure and overdue escalation tested; bell/count/list/mark-read tested; email tamper alerts and live Celery/Redis not verified) |
| 7 Reports | Dashboard KPIs and charts, PDF exports (5), audit logging | Partial (dashboard exists; five case-scoped PDFs are implemented, audit-logged, and tested; not browser-tested) |
| 8 Audit | Viewer with filters, CSV export, failed logins, integrity history, security settings, insert-only trigger | Partial (user/action/date/case filters and CSV export tested; other listed features remain) |
| 9 Search | Global search API and dropdown | Partial (grouped permission-filtered API and search input tested; authenticated dropdown and `/` shortcut not browser-tested) |
| UI | Design tokens, dark mode, responsive shell, landing, error pages, login/OTP pages | Partial |
| Security | CSRF, secure cookies, CSP, HSTS, rate limiting, input validation | Partial (CSP, production HSTS, login/OTP/upload throttles and deploy check pass; audit trigger tested on SQLite but not live PostgreSQL; input validation review remains) |
| Data | `seed_demo` (roles, cases, evidence incl. one tampered file, custody, hearings, tasks) | Complete (7 pytest; run on dev DB) |
| Tests | Route-crawl smoke test: every named no-arg URL and one instance of each detail URL, no 500s, placeholders, plain-text or non-template 200s | Complete (strict crawl passed with empty placeholder allowlist) |
| Tests | Hashing, versioning, tamper, custody, IDOR, audit immutability, uploads, reminders, status transitions, OTP/lockout, report permissions, global search | Partial (custody, notifications, tamper alerts, reminders, OTP/lockout, audit filters/export/verify, SQLite audit triggers, auth/upload rate limits, five PDF reports and report access, grouped search/access, route crawl, and seed covered; remaining cases missing) |
| Deploy | Dockerfile, docker-compose (web, nginx, postgres, redis, celery worker, beat), `.env.example` | Missing |
| Docs | README (setup, env, Celery, seed, 5-minute demo, structure) | Partial |
| QA | `manage.py check --deploy`, full test run, responsive check mobile/tablet/desktop | Missing |

## 4. HOW TO RUN
- Install: `pip install -r requirements/dev.txt` (a `.venv` already exists in the repo)
- Migrate: `python manage.py migrate`
- Seed: `python manage.py seed_demo` (idempotent; prints credentials; re-seed on a fresh DB)
- Run app: `python manage.py runserver` (settings: `evitrack.settings.development`)
- Run Redis, then start the worker with `celery -A evitrack worker -l info` and Beat with `celery -A evitrack beat -l info`; live Celery/Redis remains unverified. Production cache-backed rate limits use `EVITRACK_CACHE_URL` or `REDIS_URL`. Development email uses Django's console backend (OTP code is printed to the console); tests use locmem email. SMS uses a mock logger gateway.
- Audit viewer: `/audit/` (admin only); personal activity: `/audit/my-activity/`; filtered CSV: use Export CSV on the audit page. Reports: `/reports/` lists the five PDFs for accessible cases; every generated report is audit-logged.
- Global search: use the authenticated header box (minimum two characters); results are grouped into cases, parties and evidence, restricted to accessible cases.
- Run tests: `.venv/bin/python -m pytest` (uses `evitrack.settings.test` from `pytest.ini`)
- Run deployment checks with production settings: `EVITRACK_SECRET_KEY=<secret> ALLOWED_HOSTS=<host> python manage.py check --deploy --settings=evitrack.settings.production`.
- Demo credentials: `admin@`, `manager@`, `investigator@`, `custodian@`, `reviewer@demo.evitrack.test`, password `Demo#Pass2026`. `pending@demo.evitrack.test` cannot sign in (awaiting approval).

## 5. SESSION LOG (newest on top)
- Session 11: UI audit of existing code (grep only). Dark mode save endpoint, print CSS, branded 403/404/500 templates, session warning modal and password change view already exist. Fixed `javascript:` links in 403/404/500 and removed an unverified audit/alert claim from the 500 page. Full suite passed before the template edits; not browser-tested (no browser run this session). Next: browser check of dark mode, session modal, profile/password, and responsive pages.
- Session 10: added SQLite/PostgreSQL audit update/delete triggers and queryset/admin protection; added tested admin hash-chain verification. Rate-limited login, OTP verification and evidence upload using a shared cache (Redis-backed in production). Confirmed CSP headers and moved three inline scripts to external assets; production HSTS/X-Frame settings and `check --deploy` now pass cleanly. Full suite: 106 passed. SQLite trigger tests pass; live PostgreSQL trigger and browser flows were not tested. Next: UI leftovers.
- Session 9: implemented grouped global search for cases, parties, and evidence by evidence number/title/tag/SHA-256, scoped to the user's accessible cases. Added tests for all categories, hash/number search, inaccessible-case exclusion, unauthenticated access, short queries and header markup. Full suite: 97 passed. Preview `/dashboard/` redirected to OTP login, so authenticated search dropdown and `/` keypress were not browser-tested. Next: DB-level audit immutability and security hardening.
- Session 8: implemented admin audit viewer filters (user/action/date/case), personal access-filtered activity, and filtered CSV export. Implemented five case-scoped WeasyPrint PDFs with generated-by/date footer and report-generation audit events. All five reports return PDF and inaccessible cases return 404; route crawl passes with an empty placeholder allowlist. Full suite: 92 passed (WeasyPrint reports one HarfBuzz-Subset deprecation warning). Authenticated pages were not browser-tested. Next: global search.
- Session 7: all password logins now require a short-lived hashed email OTP; users with TOTP enabled complete an additional authenticator step. Added persistent attempt tracking and a 15-minute lock after five invalid codes, plus an additive `EmailOTPChallenge` migration. Tests cover email OTP, additional TOTP, expiry, lockout and blocking new code sends during lockout. Full suite: 76 passed; migration check reports no changes. Not browser-tested; live development console delivery was not manually exercised. Next: audit viewer and five audit-logged PDF reports.
- Session 6: reminders: implemented the Beat scanner for due email, in-app and mock-SMS delivery; fire-time deduplication; persisted retries with 5/10-minute exponential delays and a 3-attempt cap; terminal failure and overdue-task email/in-app escalation. Added five reminder tests covering default offsets, channel delivery, idempotency, backoff, escalation and overdue transition. Full suite: 72 passed. Not verified: running Celery Beat/worker with Redis, browser flows or actual external SMS delivery; SMS is intentionally mock-only. Next: email OTP on every login.
- Session 5: custody: evidence detail shows the vertical timeline and a Transfer Custody button; QR label HTML page; `apps/custody/tests` (12 pass). Notifications: unread-count JSON at `/api/notifications/unread-count/` (the bell polled a URL that did not exist); tamper alerts go to case managers via `notify_case_managers`; `apps/notifications/tests` (11 pass); evidence integrity tests (3 pass); strict crawl with placeholder allowlist. `seed_demo` with tests (7 pass), run on the dev DB. Full suite 67 pass; `manage.py check` clean; no migration drift. Not verified: authenticated pages in a browser (the login form could not be automated here; the test client covers the HTTP behaviour). Branch note in section 2.
- Session 4: added `core/dashboard.html` (role-aware KPIs, Chart.js bar charts from `api/dashboard/charts/`, `static/js/dashboard.js`); added `hearings/calendar.html` (FullCalendar, `static/js/calendar.js`), `task_create`/`task_update` via shared `task_form_base.html`; added case timeline page and partial. Route-crawl smoke test (`apps/core/tests/test_route_smoke.py`) found a `timezone.utc` 500 in the case timeline view (fixed). Tests: core, accounts, cases, evidence pass.
- Session 3: templates added for accounts (login, OTP verify, password change, profile, OTP setup, user list, approval queue, failed logins), cases (list, detail with tabs, create/edit form, party form and delete) and evidence (list, upload, detail, update, QR label); shared partials and `auth_base.html`. Fixed: `CaseAccessMixin` call sites in cases, evidence and evidence API now use module helpers (some edits had not persisted and were reapplied); evidence detail `item.versions` changed to `newer_versions`; evidence tag filter uses `evidence_items`; `self.check_case_access` calls in cases views replaced. Pytest: 30 pass. Not yet browser-tested; verify flow is fetch-based.
- Session 2: merged the new RULES, status header, run notes and log into this file; checklist rows updated from verified runs only. Case-access call sites repointed to module helpers; error and landing templates use `core:dashboard` and `core:landing`. Added `apps/cases/tests/test_case_access.py` (4 pass) and `apps/accounts/tests/test_pages.py` (8 pass, 1 fails: `accounts/login.html` missing).
- Session 1 (earlier): baseline analysis written (section 1).
