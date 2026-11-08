# EviTrack – PRODUCT SPEC (what the system must do)

Prototype built with dummy data. Out of scope: eCourts/CCTNS integration, legal advice, certified forensic acquisition. Large video files are limited by a configurable size cap.

## 1. Users and roles
| Role | Purpose |
|---|---|
| Admin | Approves users, manages roles, sees everything, audit, security settings |
| Case Manager | Manages assigned cases, assigns users, closes cases, receives integrity alerts, sees workload |
| Investigator/Advocate | Works assigned cases: parties, evidence, hearings, tasks |
| Evidence Custodian | Holds and transfers evidence on assigned cases |
| Read-only Reviewer | Views assigned cases and results; changes nothing |

Permission matrix (also shown in UI_SPEC §14):
| Capability | Admin | Case Manager | Investigator/Advocate | Custodian | Reviewer |
|---|---|---|---|---|---|
| See cases | all | own | assigned | assigned | assigned |
| Create case | ✔ | ✔ | ✖ | ✖ | ✖ |
| Edit case | ✔ | ✔ | if assigned | ✖ | ✖ |
| Assign users / close case | ✔ | ✔ | ✖ | ✖ | ✖ |
| Upload evidence / new version | ✔ | ✔ | ✔ | ✔ | ✖ |
| Request/accept custody transfer | ✔ | ✔ | ✔ | ✔ | ✖ |
| Verify integrity | ✔ | ✔ | ✔ | ✔ | view result |
| Hearings / tasks create-edit | ✔ | ✔ | ✔ | ✖ | ✖ |
| Reports | all | own cases | assigned | assigned | assigned |
| Audit log | all | own cases | ✖ | ✖ | ✖ |
| Users, approvals, security | ✔ | ✖ | ✖ | ✖ | ✖ |

## 2. Functional requirements
IDs are used in TODO files for traceability.

### Accounts and access (ACC)
- ACC-1 Register; account inactive until Admin approves; Admin can reject with reason.
- ACC-2 Login = email + password, then **email OTP on every login** (6 digits, expires, 5 wrong attempts lock for 15 minutes, resend with cooldown). Optional TOTP second step for users who enabled it.
- ACC-3 Lockout after 5 failed password attempts (15 min); failed logins visible to Admin; Admin can unlock.
- ACC-4 Session expires after 15 min inactivity; warning modal at 13 min with Stay signed in / Sign out.
- ACC-5 Profile, change password (strength rules, other sessions signed out), enable/disable TOTP, notification preferences, dark-mode preference stored per user.
- ACC-6 Role management by Admin (change role, deactivate, unlock, reset OTP).

### Cases (CAS)
- CAS-1 Create/edit case: title, type, priority (Low/Medium/High/Critical), description, opened date; auto number `EVT-YYYY-0001`.
- CAS-2 Status flow Open → Under Investigation / In Court → Closed / Archived with valid transitions only (use the transition table implemented in the cases service; changing it needs a SPEC edit).
- CAS-3 Assign users to a case with a role on the case; only Admin/Case Manager.
- CAS-4 Parties: name, type (Complainant, Accused, Witness, Client, Opposing Counsel, Other), contact, notes.
- CAS-5 List with filters (status, priority, type, assignee, text), sorting, pagination; detail with tabs Overview, Parties, Evidence, Custody, Hearings, Tasks, Timeline, Audit.
- CAS-6 Timeline merges every event for the case chronologically.
- CAS-7 Closing a case needs a reason and is Admin/Case Manager only; closed cases are read-only.

### Evidence vault (EVI)
- EVI-1 Drag-and-drop multi-file upload with progress. Server reads in 1 MB chunks, computes SHA-256, stores hash, uploader and time.
- EVI-2 Files never overwritten: a new upload becomes a new linked version.
- EVI-3 Validation: size cap, extension/MIME allowlist, random storage names, reject double extensions.
- EVI-4 Metadata and tags; evidence number auto-generated and unique.
- EVI-5 Preview (image, PDF, audio, video); every download is audit-logged.
- EVI-6 **Verify integrity**: recompute and compare; result Verified or Modified stored as IntegrityCheck; on mismatch flag the evidence, notify and email the Case Manager(s), write an audit entry.
- EVI-7 Bulk "verify all in case" runs as a background job and reports progress/result.
- EVI-8 Files live outside the public web root; served only through an authenticated, permission-checked, audit-logged endpoint.

### Chain of custody (CUS)
- CUS-1 Initial custody event on upload.
- CUS-2 Two-step handshake: holder requests transfer (receiver + reason); receiver accepts or rejects; custody moves only on accept; rejection (with reason) is logged.
- CUS-3 Vertical custody timeline per evidence item.
- CUS-4 Printable QR label: evidence no., case no., hash prefix, holder, intake date; QR links to the evidence page.
- CUS-5 Pending transfers appear on the dashboard, inbox and notifications.

### Hearings, deadlines, tasks (HEA)
- HEA-1 Calendar (month/week/list) of hearings, tasks and filing deadlines, colour-coded, permission-filtered.
- HEA-2 Create/edit hearing; record outcome and next date; offer to create the next hearing.
- HEA-3 Tasks with assignee, due date, status, filing-deadline flag; overdue highlighted.

### Reminders and notifications (NOT)
- NOT-1 Scheduled scan (Celery Beat). Defaults: hearings 7 days, 1 day, 2 hours before; deadlines 3 days and 1 day before; per-user configurable.
- NOT-2 Channels: in-app, email, SMS (mock driver). No duplicate sends.
- NOT-3 Retry failed sends with exponential backoff (max 3); escalate to Case Manager on failure or overdue task.
- NOT-4 Notification bell with unread count, dropdown, full page, mark read / mark all read.

### Dashboard and reports (REP)
- REP-1 Role-aware KPIs: open cases, hearings this week, overdue tasks, pending custody transfers, integrity alerts.
- REP-2 Charts: cases by status, cases by type, hearings per week, workload per user, evidence uploads over time.
- REP-3 Five PDF reports: case summary, evidence register (with hashes), custody history, hearing schedule, integrity report. Footer with generated-by and date; every generation is audit-logged and permission-checked.

### Audit and security (AUD)
- AUD-1 Insert-only audit log (ORM, admin, API blocked; DB trigger on PostgreSQL); hash-chained entries with an Admin "verify chain" action.
- AUD-2 Filterable viewer (user, action, date range, case) with CSV export; failed-login list; integrity-check history.
- AUD-3 CSRF, secure cookies, CSP, HSTS (production), rate limiting on login/OTP/upload, input validation, protection from IDOR, path traversal and XSS.
- AUD-4 Admin security-settings page (read-mostly) and "run integrity sweep".

### Search (SRC)
- SRC-1 Global search by case number, title, party, evidence number/title/tags/hash prefix; permission-filtered; grouped results; `/` shortcut.

## 3. Non-functional requirements
- Security first: server-side authorization on every endpoint; no secrets in the frontend; no OTP exposure.
- Performance: list endpoints paginated (default 20); `select_related`/`prefetch_related`; dashboard under ~1 s on seed data.
- Accessibility: WCAG AA, keyboard operable, focus visible, ARIA where needed.
- Responsive: 390px to 1440px+; no horizontal page scroll.
- Reliability: idempotent reminders; background jobs retry.
- Browser support: current Chrome, Edge, Firefox.

## 4. Seed/demo data
`seed_demo` creates one user per role (password `Demo#Pass2026`, emails like `admin@demo.evitrack.test`), ~8 varied cases, parties, 15+ evidence files, custody history including one pending transfer, hearings, tasks, notifications, and one deliberately tampered file. It is the only place fake data may exist.

## 5. Assumptions
- Single organisation (no multi-tenancy). English only (Hindi/Marathi are future scope).
- SMS is a mock driver; email uses the console backend in development.
- Time zone Asia/Kolkata; dates shown in the user's locale.
