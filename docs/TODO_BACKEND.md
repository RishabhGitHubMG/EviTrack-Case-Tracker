# TODO – BACKEND (API layer). Tick `[x]` only after running it. Add "(not verified: reason)" otherwise.

Priority: **H** high, **M** medium, **L** low. IDs: `BE-S<slice>-<n>`. Requirement refs in brackets point to `SPEC.md`.

## S0 Foundations
- [ ] BE-S0-01 (H) Add `drf-spectacular`, `django-filter`; configure `REST_FRAMEWORK` (session auth, pagination, filters, default permissions) and `SPECTACULAR_SETTINGS`
- [ ] BE-S0-02 (H) Create `config/api_urls.py` mounted at `/api/v1/`; add `GET /health/`, `GET /auth/csrf/`, schema endpoint
- [ ] BE-S0-03 (H) Custom exception handler producing the standard error shape and codes
- [ ] BE-S0-04 (H) Shared permission classes: `IsApprovedUser`, `HasRole`, `CaseObjectPermission` (reuse existing access helpers)
- [ ] BE-S0-05 (M) Shared pagination class and `UserRef`/`CaseRef` serializers
- [ ] BE-S0-06 (M) Test settings: file-based email backend for Playwright OTP (test/dev only, impossible in production settings) + helper docs
- [ ] BE-S0-07 (M) Tests: health, csrf, error shape, 401 shape; schema generation test

## S1 Landing
- [ ] BE-S1-01 (L) Nothing required. Confirm `/` is not captured by any API route and legacy landing still works

## S2 Authentication [ACC-1…ACC-3]
- [ ] BE-S2-01 (H) `POST /auth/register/` (validation, password rules, pending state, audit)
- [ ] BE-S2-02 (H) `POST /auth/login/` using axes + pending-auth session; masked email + expiry in response; throttled
- [ ] BE-S2-03 (H) `POST /auth/otp/verify/`, `POST /auth/otp/resend/` reusing OTP hashing/expiry/lockout; cooldown 30 s; attempts_left
- [ ] BE-S2-04 (H) `POST /auth/totp/verify/` as optional second step
- [ ] BE-S2-05 (H) `GET /auth/me/` (user, role, permissions list, preferences, counts) and `POST /auth/logout/`
- [ ] BE-S2-06 (H) `POST /auth/session/ping/` + keep server-side 15-minute idle enforcement; return `expires_in`
- [ ] BE-S2-07 (M) Permission list generation from role matrix (single source in `accounts/permissions.py`)
- [ ] BE-S2-08 (H) Tests: full login happy path, wrong password (attempts left), lockout, pending account, wrong OTP, OTP lockout, expiry, resend cooldown, TOTP step, logout, session expiry, CSRF required

## S3 App shell [ACC-5]
- [ ] BE-S3-01 (H) `PATCH /me/preferences/` (theme persisted per user)
- [ ] BE-S3-02 (H) `GET /notifications/unread-count/` (unread, pending_custody, pending_approvals for admin)
- [ ] BE-S3-03 (M) `GET /notifications/?limit=5`
- [ ] BE-S3-04 (M) `GET /search/suggest/?q=` grouped, scoped, max 5 per group
- [ ] BE-S3-05 (M) Tests: scope, preference persistence, counts per role

## S4 Dashboard [REP-1, REP-2]
- [ ] BE-S4-01 (H) `GET /dashboard/summary/` with role-aware KPIs, upcoming hearings, attention lists
- [ ] BE-S4-02 (H) `GET /dashboard/charts/` (five datasets; workload only A/M)
- [ ] BE-S4-03 (M) Query-count tests; scope tests per role; correctness checked against seed data

## S5 Cases [CAS-1…CAS-7]
- [ ] BE-S5-01 (H) Cases list/create/detail/patch with filters, search, ordering, `allowed_transitions`, `can{}`
- [ ] BE-S5-02 (H) `POST /cases/{id}/transition/` and `/close/` via service (reason required, manager only)
- [ ] BE-S5-03 (H) Assignments list/add/remove (A,M)
- [ ] BE-S5-04 (H) Parties CRUD
- [ ] BE-S5-05 (H) Timeline endpoint (merged events, type filter, pagination)
- [ ] BE-S5-06 (M) Case audit endpoint (A,M)
- [ ] BE-S5-07 (M) `GET /users/lookup/` scoped to assignable users
- [ ] BE-S5-08 (H) Tests: permission matrix across five roles, IDOR (unassigned case → 404), invalid transitions, closed case read-only, audit entries, query counts

## S6 Evidence [EVI-1…EVI-8]
- [ ] BE-S6-01 (H) Evidence list/detail/patch with filters (case, tags, type, integrity, holder, search)
- [ ] BE-S6-02 (H) `POST /evidence/` multipart upload using existing chunked-hash service; validations; version linking
- [ ] BE-S6-03 (H) `POST /evidence/{id}/verify/` returning result + created check; mismatch → flag, notify, email managers, audit
- [ ] BE-S6-04 (H) Versions and integrity-checks endpoints
- [ ] BE-S6-05 (H) `/download/` and `/preview/` streaming (X-Accel when enabled), permission + audit; correct content types for inline preview
- [ ] BE-S6-06 (M) `POST /cases/{id}/verify-all/` → 202 + `/tasks/{id}/` progress endpoint
- [ ] BE-S6-07 (M) `POST /evidence/{id}/acknowledge-alert/` and "integrity alert" flag clearing rules
- [ ] BE-S6-08 (L) `/tags/?q=` suggestions
- [ ] BE-S6-09 (H) Tests: hash correctness, new version on re-upload, tamper → Modified, upload validation (size/type/double extension), non-member 404, download audit, reviewer cannot upload

## S7 Custody [CUS-1…CUS-5]
- [ ] BE-S7-01 (H) Custody timeline endpoint
- [ ] BE-S7-02 (H) Request, accept, reject (reason), cancel via custody service; atomic; notifications + audit
- [ ] BE-S7-03 (H) Inbox endpoint (incoming/outgoing)
- [ ] BE-S7-04 (M) Label data endpoint + PDF label
- [ ] BE-S7-05 (H) Tests: handshake accept/reject, only receiver can accept, holder-only request, only case members can receive, pending visibility, rejection logged

## S8 Hearings, tasks, calendar [HEA-1…HEA-3]
- [ ] BE-S8-01 (H) `GET /calendar/events/` (range query, types, scope, overdue flag)
- [ ] BE-S8-02 (H) Hearings CRUD + reschedule + outcome with next-hearing suggestion
- [ ] BE-S8-03 (H) Tasks CRUD, mine/overdue filters, assignee toggle
- [ ] BE-S8-04 (M) Reminder rows created/updated when hearings/tasks change (reuse reminder service; idempotent)
- [ ] BE-S8-05 (H) Tests: scope, outcome flow, reschedule updates reminders, overdue calculation, reviewer read-only

## S9 Notifications and preferences [NOT-1…NOT-4]
- [ ] BE-S9-01 (H) Notifications list/filter, read, read-all
- [ ] BE-S9-02 (H) Preferences read/write incl. reminder timing, channels, phone
- [ ] BE-S9-03 (M) Test-notification endpoint
- [ ] BE-S9-04 (M) Tests: user isolation (cannot read others), preference effect on scheduling

## S10 Reports and search [REP-3, SRC-1]
- [ ] BE-S10-01 (H) Five report endpoints over existing generators; scope + audit; PDF response
- [ ] BE-S10-02 (M) `GET /reports/recent/` from audit
- [ ] BE-S10-03 (H) `GET /search/` grouped with counts, highlight snippets, hash-prefix flag
- [ ] BE-S10-04 (H) Tests: report access by role, search scope (never leaks unassigned cases), hash-prefix search

## S11 Admin and account [ACC-5, ACC-6, AUD-1…AUD-4]
- [ ] BE-S11-01 (H) Approvals list/approve(role)/reject(reason)
- [ ] BE-S11-02 (H) Users list/patch/unlock/reset-otp
- [ ] BE-S11-03 (H) Audit list with filters + CSV export; manager scope = own cases
- [ ] BE-S11-04 (H) `POST /admin/audit/verify-chain/`
- [ ] BE-S11-05 (M) Failed logins list/unlock/stats
- [ ] BE-S11-06 (M) Security settings read endpoint + integrity-sweep task
- [ ] BE-S11-07 (H) Profile GET/PATCH, password change (invalidate other sessions), TOTP enable/confirm/disable, my activity
- [ ] BE-S11-08 (H) Tests: admin-only guards, role changes audited, audit immutability still holds, chain break detected

## S12 Hardening and cutover
- [ ] BE-S12-01 (H) Verify throttles (login, OTP, register, upload) and CSP with SPA; `manage.py check --deploy` clean with 64-char key
- [ ] BE-S12-02 (H) Schema freeze check in tests (schema file matches generated types)
- [ ] BE-S12-03 (H) SPA catch-all (or nginx) for non-API paths; keep `/admin/`
- [ ] BE-S12-04 (H) Remove/relocate legacy template views only after e2e covers them; update tests
- [ ] BE-S12-05 (M) Docker/nginx: serve `frontend/dist`, proxy `/api`, keep X-Accel evidence location
- [ ] BE-S12-06 (M) Carry over unverified items: PostgreSQL audit-trigger probe, live Celery/Redis scan, Docker build (document commands for the user)
- [ ] BE-S12-07 (M) Final: full suite, migration drift check, README API section
