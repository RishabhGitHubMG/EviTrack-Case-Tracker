# EviTrack Frontend Inventory

Session 15. Source: `evitrack/urls.py` and `apps/*/urls.py` (URL names), `templates/` (template existence), and targeted reads of templates and views. Browser checks are Step 4 and are not yet run, so the "Mobile" and "Browser" columns say "not run" until Step 4 records results.

Status legend: **Complete** (template exists, feature wired, code-checked) · **Partial** (exists, with a gap listed) · **Missing** (no screen) · **Broken** (renders incorrectly or fails).

Shell status: sidebar and topbar share `templates/partials/`. Every authenticated page extends `base.html` (breadcrumbs block, `messages` partial, toast container, session modal). Auth and error pages extend `base_minimal.html` or `auth_base.html`.

## 1. Pages and routes

### 1a. Public and auth

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `core:landing` | `/` | `landing.html` | Entry page; Sign In CTA | Copy claims unbuilt features (MD5 dual hash, scheduled re-verification, dual-sign custody receipts, CJIS/ISO certification). No "How it works" section. | Partial |
| `accounts:login` | `/accounts/login/` | `accounts/login.html` (auth_base) | Landing CTA; register link | Pending-approval message is a flash message only | Complete (code) |
| `accounts:otp_verify` | `/accounts/otp/` | `accounts/otp_verify.html` | Login flow only | Email and TOTP steps share one template with an instruction line; no resend link | Complete (code) |
| `accounts:register` | `/accounts/register/` | `accounts/register.html` (base_minimal) | Login page link | Inline errors and password-strength feedback; pending approval copy is accurate. Invalid inputs and pending account state tested; browser not verified. | Complete (code) |
| `accounts:logout` | `/accounts/logout/` | view (redirect) | Topbar user menu, session modal | none | Complete |
| `errors` 403, 404, 500 | handlers | `errors/403.html`, `404.html`, `500.html` | Error handlers | Browser check not run | Complete (code) |

### 1b. Core

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `core:dashboard` | `/dashboard/` | `core/dashboard.html` | Sidebar, brand | Only 2 of 5 charts (cases by status, evidence by status). Missing: cases by type, hearings per week, workload per user, evidence uploads over time. | Partial |
| `core:search_api` | `/api/search/` | JSON | Topbar dropdown | Dropdown only; no results page | Partial |
| `core:dashboard_charts` | `/api/dashboard/charts/` | JSON | Dashboard script | Only two datasets | Partial |
| (none) | `/search/` | not built | none | Full grouped results page does not exist | Missing |

### 1c. Accounts (authenticated)

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `accounts:profile` | `/accounts/profile/` | `accounts/profile.html` | Sidebar footer, user menu | none found in review | Partial |
| `accounts:preferences` | `/accounts/preferences/` | `accounts/notification_preferences.html` | User menu "Preferences", profile | Reminder channels and timing saved; pending reminders are rescheduled | Complete (code, targeted tests; browser not verified) |
| `accounts:password_change` | `/accounts/password/` | `accounts/password_change.html` | Profile | Successful change not run in browser | Complete (code) |
| `accounts:otp_setup` | `/accounts/security/otp/` | `accounts/otp_setup.html` | Security redirect | Reached only via redirect | Partial |
| `accounts:security_settings` | `/accounts/security/` | `accounts/security.html` | Admin sidebar "Security & Policy" | Read-only settings values; admin-only access and link tested | Complete (code) |
| `accounts:user_list` | `/accounts/users/` | `accounts/user_list.html` | Admin sidebar | Search, role/status filters, approval link, and role-change form; filters and role change tested | Complete (code) |
| `accounts:user_approval` | `/accounts/users/approvals/` | `accounts/user_approval.html` | Admin sidebar, user list, dashboard card | Admin-only queue; approve/reject actions tested | Complete (code) |
| `accounts:user_approve`, `user_reject`, `user_role` | POST | view redirects | Approval and user pages | none | Complete (code) |
| `accounts:failed_logins` | `/accounts/failed-logins/` | `accounts/failed_logins.html` | Admin sidebar | Admin-only; empty state and page render tested | Complete (code) |

### 1d. Cases

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `cases:case_list` | `/cases/` | `cases/case_list.html` | Sidebar | Sort links preserve filters without duplicate sort parameters; empty-state action is role-aware. Loading state remains a polish item. | Partial |
| `cases:case_create` | `/cases/create/` | `cases/case_create.html` (extends case_form) | List "New Case" (Case Manager/Admin) | Case Manager/Admin-only access tested | Complete (code) |
| `cases:case_detail` | `/cases/<pk>/` | `cases/case_detail.html` | List rows, search, dashboard | Nine tabs (Overview, Parties, Evidence, Custody, Hearings, Tasks, Team, Timeline, Audit). Case Managers/Admins can bulk verify evidence; manager/lead party controls and assignment controls match endpoint permissions. | Partial |
| `cases:case_update` | `/cases/<pk>/edit/` | `cases/case_update.html` | Case detail | Leads can edit details but cannot close/archive; terminal status changes are limited to Case Managers/Admins and tested. | Complete (code) |
| `cases:case_assign`, `case_unassign` | POST | view redirects | Team tab | Case Managers/Admins can assign/remove; successful actions return to Team. Leads cannot assign despite case-edit privileges. Manager flow and lead denial tests pass. | Complete (code) |
| `cases:party_create`, `party_update`, `party_delete` | forms | `cases/party_form.html`, `cases/party_confirm_delete.html` | Parties tab | Create/edit/delete controls and endpoints are restricted to Case Managers/Admins/Leads; member denial tested | Complete (code) |
| `cases:case_timeline` | `/cases/<pk>/timeline/` | `cases/case_timeline.html`, `partials/timeline_content.html` | Timeline tab | none found in review | Complete (code) |

### 1e. Evidence

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `evidence:evidence_list` | `/evidence/` | `evidence/evidence_list.html` | Sidebar | Search, case, status, and tag filters; available tags are scoped to accessible cases. Filter tests pass; browser not verified. | Complete (code) |
| `evidence:evidence_upload_generic` | `/evidence/upload/` | `evidence/evidence_upload.html` | Evidence list | Single progress bar for the whole batch; no per-file progress; no drag-and-drop zone; response written with `document.write` | Partial |
| `evidence:evidence_upload` | `/evidence/upload/<case_id>/` | `evidence/evidence_upload.html` | Case Evidence tab | Same as above | Partial |
| `evidence:evidence_detail` | `/evidence/<pk>/` | `evidence/evidence_detail.html` | List, search, case tab | Verify result is not shown (page reloads); badge shows raw result text, not green Verified or red Modified; no hash copy button (SHA-256 shown as plain text); preview for image, PDF, audio, video exists | Partial |
| `evidence:evidence_update` | `/evidence/<pk>/edit/` | `evidence/evidence_update.html` | Detail (managers) | none found in review | Complete (code) |
| `evidence:evidence_download` | `/evidence/<pk>/download/` | file response | Detail | Download logging is backend | Complete (code) |
| `evidence:evidence_verify` | POST | JSON | Detail "Verify Integrity" (JS reloads page) | Result not shown inline | Partial |
| `evidence:evidence_qr` | `/evidence/<pk>/qr/` | `evidence/evidence_qr_label.html` | Detail | Browser print not run | Complete (code) |
| `evidence:evidence_preview` | `/evidence/<pk>/preview/` | file response | Detail preview | none found in review | Complete (code) |
| `evidence:evidence_bulk_verify` | `/evidence/case/<case_id>/bulk-verify/` | POST | Case Evidence tab | Case Managers/Admins see the CSRF-protected action; queued/synchronous feedback returns to Evidence. Reviewers and inaccessible users are denied. Tests pass; browser not verified. | Complete (code) |

### 1f. Custody

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `custody:custody_list` | `/custody/` | `custody/custody_list.html` | Sidebar | Pending inbox and history table present | Complete (code) |
| `custody:custody_request` | `/custody/evidence/<id>/request/` | `custody/custody_request.html` | Evidence detail | none found in review | Complete (code) |
| `custody:custody_respond` | `/custody/<pk>/respond/` | `custody/custody_respond.html` | Inbox card | Accept and reject modals present | Complete (code) |
| `custody:custody_timeline` | `/custody/evidence/<id>/timeline/` | `custody/custody_timeline.html` | Not linked | Fragment with no `extends`: the route returns bare HTML with no sidebar, topbar or styles | Broken |
| `custody:custody_qr_label` | `/custody/evidence/<id>/label/` | `custody/qr_label.html` | Custody list row action | Print styles to check in Step 4 | Complete (code) |

### 1g. Hearings and tasks

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `hearings:hearing_list` | `/hearings/` | `hearings/hearing_list.html` | Sidebar | Outcome column and Calendar View link | Partial |
| `hearings:calendar` | `/hearings/calendar/` | `hearings/calendar.html` | Hearing list, task list | Month, week, list views; case selector and date-click hearing creation; existing hearing events open detail, which links to edit. Read-only reviewers cannot create, edit, or record outcomes. Five route/template tests pass; browser not verified. | Complete (code) |
| `hearings:hearing_create` | `/hearings/case/<case_id>/new/` | `hearings/hearing_create.html` | Case Hearings tab, calendar case selector/date click | Calendar date is prefilled on the form | Complete (code) |
| `hearings:hearing_detail` | `/hearings/<pk>/` | `hearings/hearing_detail.html` | List, calendar events | Outcome modal (`hearing_outcome`) with next hearing date and Edit Hearing action | Complete (code) |
| `hearings:hearing_update` | `/hearings/<pk>/edit/` | `hearings/hearing_update.html` | Detail | none found in review | Complete (code) |
| `hearings:hearing_outcome` | POST | view | Detail modal | none found in review | Complete (code) |
| `hearings:task_list` | `/hearings/tasks/` | `hearings/task_list.html` | Sidebar | Overdue filter, overdue row highlight and filing-deadline badge present | Partial |
| `hearings:task_create`, `task_update` | forms | `hearings/task_form_base.html` (and children) | Task list, case Tasks tab | none found in review | Complete (code) |
| `hearings:task_status` | POST | view | Task list status select | none found in review | Complete (code) |

### 1h. Notifications, reports, audit

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `notifications:notification_list` | `/notifications/` | `notifications/notification_list.html` | Sidebar, bell | Read-state (all/read/unread) and type filters; Mark all read and Mark read present. Filter tests pass; browser not verified. | Complete (code) |
| `notifications:notification_detail` | `/notifications/<pk>/` | open view (redirect) | Bell items | none found in review | Complete (code) |
| `notifications:notification_mark_read`, `mark_all_read` | POST | views | Notification page | none found in review | Complete (code) |
| `reports:report_list` | `/reports/` | `reports/report_list.html` | Sidebar | Accessible-case picker supports one case or all; five PDF actions are tested. Browser not verified. | Complete (code) |
| `reports:case_summary`, `evidence_register`, `custody_history`, `hearing_schedule`, `integrity_report` | `/reports/cases/<id>/*.pdf` | PDF response | Report list | Tested in pytest; not browser-checked | Complete (code) |
| `audit:audit_log_list` | `/audit/` | `audit/audit_log_list.html` | Admin sidebar | User, action, case, and date filters; CSV export and POST verify-chain action tested; admin-only access. Browser not verified. | Complete (code) |
| `audit:my_activity` | `/audit/my-activity/` | `audit/audit_log_list.html` | Topbar user menu | Same template as audit log | Complete (code) |
| `audit:audit_log_export` | `/audit/export.csv` | CSV response | Audit page | none found in review | Complete (code) |

### 1i. Missing screens (required by the spec)

| Screen | Gap | Status |
|---|---|---|
| Search results page (`/search/`) | Grouped case/party/evidence results scoped to accessible cases | Complete (code; browser not verified) |
| Notification preferences | Persistent channel/timing fields, dedicated form/page, reminder rescheduling | Complete (code; browser not verified) |
| Security & Policy page | Admin-only read-only settings page linked from the sidebar | Complete (code) |
| Verify-chain control on audit page | Admin-only POST button on the audit log | Complete (code) |
| Calendar create and edit | Calendar date-click schedules; events open hearing detail with edit action | Complete (code; browser not verified) |

## 2. Shell

| Component | Where | Status | Gap |
|---|---|---|---|
| Collapsible sidebar, mobile drawer | `partials/sidebar.html`, `static/js/evitrack.js` | Partial | Admin approval, failed-login, audit, and security links are present; responsive browser check remains |
| Topbar global search, `/` shortcut, grouped dropdown | `partials/topbar.html`, `evitrack.js` | Partial | No full page; no arrow-key navigation |
| Notification bell and dropdown | `partials/topbar.html`, polling in `evitrack.js` | Complete (code) | Sidebar count not refreshed by polling |
| User menu | `partials/topbar.html` | Complete (code) | Preferences opens the dedicated notification settings page |
| Dark mode toggle | `topbar.html`, `evitrack.js` (persists via `accounts_api:preferences_theme`) | Complete (code) | Browser check not run |
| Breadcrumbs | `topbar.html` block `breadcrumbs` | Complete (code) | Public pages have none (by design) |
| Toasts | `#evToastContainer`, `EviTrack.showToast` | Partial | Toast message is inserted as HTML; callers must escape |
| Session timeout modal | `base.html`, `evitrack.js` | Complete (code) | Browser check: warning at 13 min, redirect at 15 min (session 12) |

## 3. Polish gaps across templates

| Area | Finding |
|---|---|
| Loading states | No skeleton or spinner pattern exists in any template. |
| Sticky table headers | None defined. |
| Empty states | `partials/empty_state.html` used on list pages. Calls to action present on some pages only. |
| Error states | Form and message alerts only. No retry or inline API error UI on tables. |
| Mobile | `table-responsive` on list tables. Browser check at 390 px not yet run (Step 4). |
| Accessibility | Focus ring added in session 12. Contrast ratios not checked. |
| Fonts | `base.html` loads Inter, Source Serif 4, JetBrains Mono. Heading use to verify in Step 3. |

## 4. Verification log

| Date / step | What was run | Result |
|---|---|---|
| Session 13, Step 1 | Route list from urls.py; template grep matrix; targeted reads of base, sidebar, topbar, dashboard, case detail, evidence detail, upload, calendar, custody timeline view, core views, JS | Inventory recorded. No browser run yet. |
| Session 16–17, Steps 2 batches 4–5 | Admin/audit/account/case/report page and action tests; reports case-picker, five PDFs, audit logging, access denial | Targeted tests passed; full suite 165 passed. Browser checks remain unverified because Playwright is unavailable. |

## 4a. Step 2, batch 1 (session 13)

Tables in sections 1 and 2 reflect the Step 1 inventory. These changes are done since then. Status is code-level: pytest passes, and no browser run has been done yet.

| Item | Change | Status |
|---|---|---|
| Landing | Removed unbuilt claims; added How it works section and Sign in CTA | Complete (code) |
| Custody timeline route | Page template extends base; partial reused | Complete (code), 2 tests |
| Search results | `/search/` page, grouped by Cases/Parties/Evidence, scoped to accessible cases; topbar Enter key and "See all results" link | Complete (code), 4 tests |
| Evidence detail | Green Verified and red Modified badges; hash copy button; verify result shown inline | Complete (code) |
| Evidence upload | Drop zone, per-file queue with progress, one request per file; failures read from server messages | Complete (code), browser not run |
| Audit verify chain | POST button on audit log (admin), uses `AuditLog.verify_chain` | Complete (code), 3 tests |
| Security & Policy | Read-only page with live settings values (admin) | Complete (code), 4 tests with sidebar links |
| Sidebar admin links | Approval Queue and Failed Logins added | Complete (code) |
| Dashboard charts | Added cases by type, hearings per week, open tasks per team member, evidence uploads per week | Complete (code), 3 tests |

Still open after Step 2 batches 1–4:

- Integrated UI review of search, custody, dashboard, evidence, and landing (TODO T10).
- Design polish and desktop/mobile browser checks, including screenshots and dead-link crawl (TODO T11–T14); Playwright unavailable in session 16.
- Docker/Celery/PostgreSQL, README, status reconciliation, and final QA (TODO T15–T25).

## 4b. Step 2, batch 2 (session 14)

Added the dedicated notification preferences page using existing user preference fields, with an additive migration for defaults and rescheduling of pending reminders after changes. The calendar now supports case-scoped hearing creation, date prefill from clicked dates, and event-to-detail/edit navigation. Notification listing now filters by read state and type. Targeted tests passed (19 account/reminder, 5 calendar including reviewer restrictions, 15 notification tests); full suite passed (147 tests), `manage.py check`, migration check, and Node syntax check passed. Browser checks are not verified because Playwright is unavailable in this environment.

## 4c. Step 2, batch 3 (session 15)

Added the evidence tag selector (the backend filter already existed), tested matching results and tag scoping to accessible cases; added case Evidence bulk verification with CSRF, correct tab return, and reviewer/inaccessible-case denial; reconciled assignment visibility with Case Manager/Admin endpoint permissions and tested manager assign/remove plus case-lead denial. Targeted tests passed (7 evidence-page, 5 integrity, 2 assignment); full suite passed (153 tests), with Django and migration checks clean. Browser verification is not verified because Playwright is unavailable.

## 4d. Step 2, batch 4 (session 16)

Checked admin and audit navigation/access/actions, then fixed account/case gaps found during review: approval and rejection now accept only same-host return URLs; registration approval copy is accurate; user listing has status and role controls; case creation and close/archive transitions follow the documented role policy; case sorting preserves filters; and party controls/endpoints are limited to managers, admins, and case leads. Targeted tests passed (41 admin/audit, 21 account/case); full suite passed (164 tests), and Django/migration checks passed. Browser checks remain unverified because Playwright is unavailable.

## 4e. Step 2, batch 5 (session 17)

Added a case picker to the reports page, preserving all-accessible-cases behavior and providing a clear filter action. Tests verify selected/inaccessible cases, all five PDF links and exports, report audit events, and 404 for inaccessible case reports. Targeted tests passed (17); full suite passed (165 tests), with Django and migration checks clean. Browser verification remains unverified because Playwright is unavailable.

## 5. Blocked commands

- Session 13: a Bash command that used shell command substitution to loop over templates was blocked by the environment's injection policy. It was not retried. The equivalent checks were done with the Grep and Read tools.
