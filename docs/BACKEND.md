# EviTrack – BACKEND ARCHITECTURE (Django API layer for the React SPA)

The Django backend already exists: apps `accounts, cases, evidence, custody, hearings, notifications, reports, audit, core`, a service layer, Celery, seed data and 118+ tests. This file defines the **new JSON API layer** added on top. Do not rewrite working business logic.

## 1. Principles
1. **Thin API, fat services.** API views validate input, call the existing service functions, and serialise output. Business rules (status transitions, custody handshake, hashing, reminder scheduling, audit logging) stay in `services.py` modules and are shared with legacy views.
2. **Authorization on the server, always.** Querysets are scoped per user with the existing case-access helpers; object permissions are checked on detail and write endpoints; unassigned objects return 404 (preferred, avoids leaking existence) or 403 for known-visible objects.
3. **One API version:** everything under `/api/v1/`. Same-origin session auth (cookie + CSRF), no JWT.
4. **Contract-first friendly:** schema generated with `drf-spectacular` (added dependency; justified by the TypeScript type generation). `docs/API_CONTRACT.md` is the human summary.
5. **Legacy keeps working** until the cutover slice. API code lives beside it, not instead of it.

## 2. Layout
Each app gets an `api/` package:
```
apps/<app>/api/
  __init__.py
  serializers.py   # input and output serializers (separate when shapes differ)
  views.py         # APIView / ViewSet, thin
  permissions.py   # app-specific permission classes (optional)
  filters.py       # django-filter FilterSets
  urls.py          # router + paths
apps/core/api/      # dashboard, search, session ping, shared pagination/errors/permissions
config/api_urls.py  # includes every app's urls under /api/v1/
```
Existing `apps/audit` and others may already use different names; follow the repo's real structure and record it in `PROGRESS.md`.

## 3. Conventions
- **Auth classes:** `SessionAuthentication` with CSRF enforced. `GET /api/v1/auth/csrf/` sets the cookie for the SPA.
- **Permissions:** default `IsAuthenticated` + `IsApprovedUser`; add `HasRole([...])` and `CaseObjectPermission` (view/edit/manage levels using the existing helpers).
- **Pagination:** page-number, default 20, max 100: `{count, next, previous, results}`.
- **Filtering/search/order:** `django-filter` + `SearchFilter` + `OrderingFilter` with explicit allowlists.
- **Error shape (all errors):**
```json
{ "code": "validation_error", "message": "Please fix the highlighted fields.",
  "fields": { "title": ["This field is required."] }, "retry_after": null }
```
Codes: `validation_error, not_authenticated, permission_denied, not_found, throttled, otp_required, otp_invalid, otp_locked, account_pending, account_locked, conflict, server_error`. Implement via a custom DRF exception handler; never leak stack traces.
- **Dates:** ISO 8601 with timezone. **IDs:** integers, plus human numbers (`case_no`, `evidence_no`) in payloads.
- **Writes return the updated object**; actions (verify, accept, close) return the new state plus any created side-objects (e.g. IntegrityCheck).
- **Audit:** every state-changing endpoint calls the existing audit helper with user, IP, user agent, object, case. Downloads, reports and verifications are audited.
- **Transactions:** wrap multi-step writes (custody accept, upload version) in `transaction.atomic`.
- **N+1:** `select_related` / `prefetch_related` in every list view; add a query-count test for the heavy lists (cases, evidence, dashboard).

## 4. Authentication flow (API)
State is kept server-side (session) so refresh and multiple tabs behave.
1. `POST /auth/login/` {email, password} → throttled; on success sets a **pending-auth** session and returns `{status:"otp_required", otp:{sent_to_masked, expires_in, resend_in}}`. If TOTP is enabled the later step is `totp_required`. Pending/locked accounts return `account_pending` / `account_locked`.
2. `POST /auth/otp/verify/` {code} → on success returns `{status:"authenticated"}` or `{status:"totp_required"}`; wrong codes decrement attempts; 5 wrong → `otp_locked` (15 min).
3. `POST /auth/otp/resend/` → cooldown 30 s.
4. `POST /auth/totp/verify/` {code} → authenticated.
5. `GET /auth/me/` → user, role, permissions, preferences, or 401.
6. `POST /auth/logout/`; `POST /auth/session/ping/` extends inactivity timer; server also enforces the 15-minute idle timeout (existing middleware).
7. `POST /auth/register/`, `POST /auth/password/change/`, `POST/DELETE /auth/totp/` (enable/disable).
Reuse existing `django-axes`, OTP code hashing/expiry/lockout logic and the session-timeout middleware; the API only exposes them.
**OTP exposure:** never in responses. For Playwright, set `EVITRACK_PLAYWRIGHT_EMAIL_DIR` in development or test settings to write messages to that directory; production settings ignore this variable and use SMTP or the configured production backend.

## 5. Files and uploads
- `POST /evidence/` multipart (`file`, `case`, `title`, `tags`, optional `new_version_of`). The existing chunked-hash service computes SHA-256 while saving to `EVIDENCE_ROOT` under a random name; validation (size cap, allowlist, double extension) runs before saving; response includes the hash and version.
- Multiple files = multiple requests (the SPA tracks progress per file).
- `GET /evidence/{id}/download/` and `/preview/` stream through Django (`X-Accel-Redirect` when `EVIDENCE_USE_X_ACCEL` is on), require the session cookie, check case permission and write an audit entry. They must work from `<img>`, `<audio>`, `<video>` and `<iframe>` tags on the same origin.

## 6. Background and long-running work
- Bulk verify and report generation may run as Celery tasks. API returns `202` with `{task_id, status_url}`; `GET /tasks/{id}/` returns `{state, progress, result}`. Where WeasyPrint is fast, PDFs may be returned directly (`Content-Disposition: attachment`).
- Reminder scanning stays on Celery Beat; the API only exposes preferences and notifications.

## 7. Security
- CSRF on all unsafe methods; CORS **disabled** (same-origin through the Vite proxy / nginx). Cookies: `HttpOnly`, `Secure` (production), `SameSite=Lax`.
- Throttles: login, OTP verify/resend, register, upload (reuse existing rate-limit helpers; return `429` with `retry_after`).
- CSP stays strict (self-hosted fonts and scripts). The SPA must not need inline scripts.
- No object enumeration: list endpoints always scoped; search results scoped.
- Audit log remains insert-only; no API endpoint can change it. `verify-chain` is read-only.

## 8. Testing
- `pytest` API tests per endpoint: success, validation errors, unauthenticated (401), wrong role (403), other user's object (404), throttling where relevant, audit entry created where relevant.
- Permission matrix test: parametrised over the five roles for each resource family (mirror `SPEC.md` §1).
- Contract test: schema generation succeeds and is stored/checked (fail CI if the schema changes without regenerating types).
- Query-count tests for heavy lists.
- Keep all existing tests green until cutover.

## 9. Settings
`drf-spectacular` in `INSTALLED_APPS`; `REST_FRAMEWORK` default classes as above; `SPECTACULAR_SETTINGS` (title, version, `COMPONENT_SPLIT_REQUEST=True`); schema at `/api/schema/` (DEBUG only or admin-only in production); docs UI optional in DEBUG.
`django-filter` added if not present. No other new dependency without justification.

## 10. Cutover support (slice S12)
Add a catch-all that serves the built SPA `index.html` for non-API, non-admin, non-static paths (or let nginx do it). Keep `/admin/` (Django admin, read-only for AuditLog). Remove or relocate legacy template views only when e2e + API tests cover the same behaviour.
