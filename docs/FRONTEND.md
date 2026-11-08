# EviTrack Frontend Inventory

Session 13. Source: `evitrack/urls.py` and `apps/*/urls.py` (URL names), `templates/` (template existence), and targeted reads of templates and views. Browser checks are Step 4 and are not yet run, so the "Mobile" and "Browser" columns say "not run" until Step 4 records results.

Status legend: **Complete** (template exists, feature wired, code-checked) · **Partial** (exists, with a gap listed) · **Missing** (no screen) · **Broken** (renders incorrectly or fails).

Shell status: sidebar and topbar share `templates/partials/`. Every authenticated page extends `base.html` (breadcrumbs block, `messages` partial, toast container, session modal). Auth and error pages extend `base_minimal.html` or `auth_base.html`.

## 1. Pages and routes

### 1a. Public and auth

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `core:landing` | `/` | `landing.html` | Entry page; Sign In CTA | Copy claims unbuilt features (MD5 dual hash, scheduled re-verification, dual-sign custody receipts, CJIS/ISO certification). No "How it works" section. | Partial |
| `accounts:login` | `/accounts/login/` | `accounts/login.html` (auth_base) | Landing CTA; register link | Pending-approval message is a flash message only | Complete (code) |
| `accounts:otp_verify` | `/accounts/otp/` | `accounts/otp_verify.html` | Login flow only | Email and TOTP steps share one template with an instruction line; no resend link | Complete (code) |
| `accounts:register` | `/accounts/register/` | `accounts/register.html` (base_minimal) | Login page link | Needs inline validation check and layout review | Partial |
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
| `accounts:preferences` | `/accounts/preferences/` | redirect to profile | User menu "Preferences" | No notification preferences (reminder timing, channels) | Missing |
| `accounts:password_change` | `/accounts/password/` | `accounts/password_change.html` | Profile | Successful change not run in browser | Complete (code) |
| `accounts:otp_setup` | `/accounts/security/otp/` | `accounts/otp_setup.html` | Security redirect | Reached only via redirect | Partial |
| `accounts:security_settings` | `/accounts/security/` | redirect to otp_setup | Sidebar "Security & Policy" (admin) | No security settings page | Missing |
| `accounts:user_list` | `/accounts/users/` | `accounts/user_list.html` | Sidebar (admin) | Role filter and status filter present; no link to approvals or failed logins | Partial |
| `accounts:user_approval` | `/accounts/users/approvals/` | `accounts/user_approval.html` | Dashboard card only | Not in sidebar | Partial |
| `accounts:user_approve`, `user_reject`, `user_role` | POST | view redirects | Approval and user pages | none | Complete (code) |
| `accounts:failed_logins` | `/accounts/failed-logins/` | `accounts/failed_logins.html` | Not linked | Not in sidebar or user pages | Partial |

### 1d. Cases

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `cases:case_list` | `/cases/` | `cases/case_list.html` | Sidebar | Column header sort links append a duplicate `sort`/`dir` query; no empty-state action; no loading state | Partial |
| `cases:case_create` | `/cases/create/` | `cases/case_create.html` (extends case_form) | List "New Case" | none found in review | Complete (code) |
| `cases:case_detail` | `/cases/<pk>/` | `cases/case_detail.html` | List rows, search, dashboard | Nine tabs (Overview, Parties, Evidence, Custody, Hearings, Tasks, Team, Timeline, Audit). No bulk verify control on Evidence tab. Assign/unassign UI not checked. | Partial |
| `cases:case_update` | `/cases/<pk>/edit/` | `cases/case_update.html` | Case detail | Status dropdown limited to allowed transitions (form logic) | Complete (code) |
| `cases:case_assign`, `case_unassign` | POST | view redirects | Team tab (not verified) | Assign UI not verified | Partial |
| `cases:party_create`, `party_update`, `party_delete` | forms | `cases/party_form.html`, `cases/party_confirm_delete.html` | Parties tab | Party create form is inside the tab | Complete (code) |
| `cases:case_timeline` | `/cases/<pk>/timeline/` | `cases/case_timeline.html`, `partials/timeline_content.html` | Timeline tab | none found in review | Complete (code) |

### 1e. Evidence

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `evidence:evidence_list` | `/evidence/` | `evidence/evidence_list.html` | Sidebar | Filters and tag filter to confirm in Step 2 | Partial |
| `evidence:evidence_upload_generic` | `/evidence/upload/` | `evidence/evidence_upload.html` | Evidence list | Single progress bar for the whole batch; no per-file progress; no drag-and-drop zone; response written with `document.write` | Partial |
| `evidence:evidence_upload` | `/evidence/upload/<case_id>/` | `evidence/evidence_upload.html` | Case Evidence tab | Same as above | Partial |
| `evidence:evidence_detail` | `/evidence/<pk>/` | `evidence/evidence_detail.html` | List, search, case tab | Verify result is not shown (page reloads); badge shows raw result text, not green Verified or red Modified; no hash copy button (SHA-256 shown as plain text); preview for image, PDF, audio, video exists | Partial |
| `evidence:evidence_update` | `/evidence/<pk>/edit/` | `evidence/evidence_update.html` | Detail (managers) | none found in review | Complete (code) |
| `evidence:evidence_download` | `/evidence/<pk>/download/` | file response | Detail | Download logging is backend | Complete (code) |
| `evidence:evidence_verify` | POST | JSON | Detail "Verify Integrity" (JS reloads page) | Result not shown inline | Partial |
| `evidence:evidence_qr` | `/evidence/<pk>/qr/` | `evidence/evidence_qr_label.html` | Detail | Browser print not run | Complete (code) |
| `evidence:evidence_preview` | `/evidence/<pk>/preview/` | file response | Detail preview | none found in review | Complete (code) |
| `evidence:evidence_bulk_verify` | `/evidence/case/<case_id>/bulk-verify/` | POST | No button found in templates | No UI control | Missing |

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
| `hearings:calendar` | `/hearings/calendar/` | `hearings/calendar.html` | Hearing list, task list | Month, week, list views in FullCalendar. Events colour-coded (hearing navy, task amber, filing deadline red) in the API. No create or edit from the calendar. | Partial |
| `hearings:hearing_create` | `/hearings/case/<case_id>/new/` | `hearings/hearing_create.html` | Case Hearings tab | Not reachable from calendar | Complete (code) |
| `hearings:hearing_detail` | `/hearings/<pk>/` | `hearings/hearing_detail.html` | List, calendar events | Outcome modal (`hearing_outcome`) with next hearing date | Complete (code) |
| `hearings:hearing_update` | `/hearings/<pk>/edit/` | `hearings/hearing_update.html` | Detail | none found in review | Complete (code) |
| `hearings:hearing_outcome` | POST | view | Detail modal | none found in review | Complete (code) |
| `hearings:task_list` | `/hearings/tasks/` | `hearings/task_list.html` | Sidebar | Overdue filter, overdue row highlight and filing-deadline badge present | Partial |
| `hearings:task_create`, `task_update` | forms | `hearings/task_form_base.html` (and children) | Task list, case Tasks tab | none found in review | Complete (code) |
| `hearings:task_status` | POST | view | Task list status select | none found in review | Complete (code) |

### 1h. Notifications, reports, audit

| URL name | Path | Template | Linked from | Gaps | Status |
|---|---|---|---|---|---|
| `notifications:notification_list` | `/notifications/` | `notifications/notification_list.html` | Sidebar, bell | No filters (read state, type); Mark all read and Mark read present | Partial |
| `notifications:notification_detail` | `/notifications/<pk>/` | open view (redirect) | Bell items | none found in review | Complete (code) |
| `notifications:notification_mark_read`, `mark_all_read` | POST | views | Notification page | none found in review | Complete (code) |
| `reports:report_list` | `/reports/` | `reports/report_list.html` | Sidebar | Case table with five PDF buttons per case. Spec asks for a case picker; current layout is a list of all accessible cases. | Partial |
| `reports:case_summary`, `evidence_register`, `custody_history`, `hearing_schedule`, `integrity_report` | `/reports/cases/<id>/*.pdf` | PDF response | Report list | Tested in pytest; not browser-checked | Complete (code) |
| `audit:audit_log_list` | `/audit/` | `audit/audit_log_list.html` | Sidebar (admin) | Filters (user, action, date range) and CSV export present. No verify-chain button; verification exists only as Django admin action. | Partial |
| `audit:my_activity` | `/audit/my-activity/` | `audit/audit_log_list.html` | Topbar user menu | Same template as audit log | Complete (code) |
| `audit:audit_log_export` | `/audit/export.csv` | CSV response | Audit page | none found in review | Complete (code) |

### 1i. Missing screens (required by the spec)

| Screen | Gap | Status |
|---|---|---|
| Search results page (`/search/`) | Not built. Only the topbar dropdown exists. | Missing |
| Notification preferences | No model or form. Current "Preferences" links to profile. | Missing |
| Security & Policy page | Sidebar link redirects to OTP setup. | Missing |
| Verify-chain control on audit page | Admin action only | Missing |
| Calendar create and edit | Not built | Missing |

## 2. Shell

| Component | Where | Status | Gap |
|---|---|---|---|
| Collapsible sidebar, mobile drawer | `partials/sidebar.html`, `static/js/evitrack.js` | Partial | Admin links for approvals and failed logins absent |
| Topbar global search, `/` shortcut, grouped dropdown | `partials/topbar.html`, `evitrack.js` | Partial | No full page; no arrow-key navigation |
| Notification bell and dropdown | `partials/topbar.html`, polling in `evitrack.js` | Complete (code) | Sidebar count not refreshed by polling |
| User menu | `partials/topbar.html` | Partial | "Preferences" link goes to profile |
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

Still open in Step 2:

- Notification preferences (reminder timing and channels): needs a model, migration and scheduler hook. The current "Preferences" link still goes to profile. This is a backend change and is not yet made.
- Calendar create and edit: not built.
- Notification list filters (read state, type): not built.
- Evidence list tag filter: not confirmed.
- Bulk verify control on the case Evidence tab: no button yet (`evidence:evidence_bulk_verify` exists).
- Case assign and unassign UI: not verified.
- Mobile and desktop checks of all changed pages: Step 4.

## 5. Blocked commands

- Session 13: a Bash command that used shell command substitution to loop over templates was blocked by the environment's injection policy. It was not retried. The equivalent checks were done with the Grep and Read tools.
