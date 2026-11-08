# EviTrack – UX (how people move through the product)

Visual details live in `UI_SPEC.md`. This file defines journeys, navigation, behaviour rules and wording. Tone: calm, precise, trustworthy; plain words, no jargon without a tooltip.

## 1. Personas (use the demo users)
| Persona | Goal | Typical day |
|---|---|---|
| **Admin** (Meera) | Keep the system safe and people onboarded | Approves sign-ups, checks failed logins, verifies audit chain |
| **Case Manager** (Rahul) | Keep every case on track | Reviews dashboard, assigns people, reacts to integrity alerts, reads reports |
| **Investigator/Advocate** (Anita) | Build the case file | Adds parties, uploads evidence, schedules hearings, completes tasks |
| **Evidence Custodian** (Vikram) | Protect physical-to-digital handover | Accepts transfers, verifies files, prints QR labels |
| **Reviewer** (Priya) | Inspect without changing | Browses cases, reads reports |

## 2. Site map and routes
```
PUBLIC     /                  Landing
           /login             Sign in (email + password)
           /login/otp         Email code
           /login/totp        Authenticator code (only if enabled)
           /register          Request access
           /register/pending  "Awaiting approval"
APP        /dashboard
           /cases             /cases/new   /cases/:id?tab=…   /cases/:id/edit
           /evidence          /evidence/:id?tab=…
           /custody/inbox     /custody/:evidenceId/label
           /calendar          /tasks
           /notifications     /preferences
           /reports           /search?q=
           /profile           /password
ADMIN      /admin/approvals   /admin/users   /admin/audit
           /admin/failed-logins   /admin/security
SYSTEM     403   404   500   /session-expired
```
Unknown paths show the 404 page. Signed-out users who open an app route go to `/login` and return to the page they wanted after signing in (`?next=`). Signed-in users who open `/login` go to `/dashboard`.

## 3. Primary journeys (each becomes a Playwright e2e test)
### J1 First-time visitor → access
Landing → reads hero and features → **Request access** → register form (inline validation, password strength meter) → "Request sent" page explaining approval → email-less wait. If they try to sign in before approval: friendly amber panel "Your account is awaiting approval", never an error message.
### J2 Sign in (every time)
Login → correct password → OTP page ("We sent a 6-digit code to a***@…", 6 boxes, resend with 30 s cooldown, expiry timer) → (optional TOTP page) → Dashboard. Wrong password shows attempts left; 5 failures show a locked state with countdown. Wrong code shows attempts left; 5 wrong codes lock for 15 minutes.
### J3 Investigator builds a case file
Dashboard → **New case** → form → case detail (Overview) → Parties tab → add party (modal) → Evidence tab → **Upload** (drop zone, per-file progress, hash shown when done) → Hearings tab → schedule hearing (reminders preselected) → Tasks tab → add filing deadline.
### J4 Custodian handles a transfer
Notification bell shows "Transfer requested" → Custody inbox → Incoming card shows evidence, hash, reason → **Accept** (or Reject with reason) → custody timeline updates → print QR label.
### J5 Manager reacts to tampering
Verify integrity on an evidence file → result animates to red **Modified** → red banner on the page, toast, notification to managers, pinned alert on the dashboard → manager opens evidence → sees side-by-side hash comparison and history → acknowledges alert → audit entry recorded.
### J6 Hearing outcome
Calendar → click hearing → drawer → **Record outcome** → choose outcome, set next date → prompt "Create the next hearing on 12 Mar?" → Create now.
### J7 Admin onboarding and oversight
Sidebar badge → Approvals → choose final role → Approve → toast. Later: Audit log → filter by case → Export CSV → **Verify audit chain** → green "Chain intact" or red "Break detected".
### J8 Report
Reports → pick case → Download PDF (spinner → toast) → opens file; shows up in "Recent reports".

## 4. Navigation rules
- Sidebar groups: Workspace, Custody, Insights, Administration. Items the role cannot use are **hidden**, not disabled.
- Active item has an amber bar and `aria-current="page"`; counts appear as badges (pending custody, approvals, unread).
- Breadcrumbs on every app page; the last crumb is plain text.
- Tabs reflect in the URL (`?tab=evidence`) so refresh and sharing work; switching tabs keeps scroll position.
- Back button always behaves; modals do not create history entries except detail drawers (which do).
- Filters live in the URL query string and survive refresh.

## 5. Interaction patterns
- **Forms:** validate on blur and on submit; errors are inline with an icon and text, linked by `aria-describedby`; first invalid field is focused; submit button shows a spinner and cannot double-submit; unsaved-changes warning on leave.
- **Tables/lists:** sticky header, sortable columns, server pagination, skeleton on first load, subtle inline spinner on refetch (keep old rows visible), empty state with a call to action, error state with **Try again**.
- **Destructive or irreversible actions** (close case, reject transfer, delete task/party, deactivate user): confirm dialog stating the consequence; confirm button is red.
- **Optimistic updates** only for low-risk toggles (mark notification read, task checkbox, dark mode). Never for evidence, custody, verification, status changes or anything audited: wait for the server.
- **Long operations** (bulk verify, PDF generation): show progress in a toast or card; the user can keep navigating; result arrives as a toast and a notification.
- **Real-time-ish:** poll unread count every 60 s and on window focus; no websockets.
- **Copy actions** (hash, case number) always confirm with a "Copied" toast.
- **Keyboard:** `/` search, `g d` dashboard, `g c` cases, `Esc` closes overlays, `?` shortcut sheet. All dialogs trap focus and restore it.

## 6. Feedback and error handling
| Situation | Behaviour |
|---|---|
| Action succeeded | Toast (4 s), UI updates in place |
| Field validation error from API | Map `fields` to inputs; summary on top if > 2 |
| 401 (session ended) | Save current path, go to `/session-expired` → Sign in again → return |
| 403 | 403 page for navigation; toast "You don't have permission" for in-page actions |
| 404 | 404 page; stale links to deleted objects explain "This item no longer exists" |
| 429 (rate limit) | Inline message with retry-after seconds, button disabled until then |
| Network failure | Banner "You appear to be offline. Changes were not saved." with Retry |
| 500 | 500 page; never show stack traces or internal ids |
| Upload failure | Row turns red with the reason and a Retry button; other files continue |

## 7. Loading strategy
Route-level code splitting with a skeleton shell. Each page shows layout-matching skeletons, never a blank screen or a lone spinner. Prefetch the next likely page on hover for sidebar links. Charts load after KPIs.

## 8. Wording guide
- Buttons are verbs: **Request access, Upload evidence, Verify integrity, Accept transfer**.
- Explain technical terms on hover: *SHA-256 fingerprint: a unique code calculated from the file. If even one byte changes, the code changes.*
- Status words: Verified, Modified, Never verified, Pending, Accepted, Rejected, Overdue, Due soon.
- Empty states: say what belongs here and offer the action ("No evidence yet. Upload the first file.").
- Errors say what happened and what to do next; never blame the user.
- Dates: relative for recent ("2 h ago") with exact time on hover; absolute for hearings ("Tue 12 Mar, 10:30").

## 9. Role-aware UX
- Dashboard content, sidebar items and action buttons follow the permission matrix in `SPEC.md` §1.
- Reviewer sees the same screens in read-only mode; write controls are hidden and a small "Read-only access" pill appears in the user card.
- Case Manager sees the Workload chart and the integrity-alert card; Admin additionally sees the Awaiting approval card.

## 10. Responsive behaviour
- Mobile: sidebar becomes a drawer; tables become cards or scroll with a sticky first column; tabs become a scrollable strip; calendar defaults to List; modals become full-height sheets; primary action becomes a floating button where a page has one clear action.
- Tablet: sidebar collapses to an icon rail.
- Nothing may scroll horizontally at the page level.

## 11. Accessibility behaviours
Skip link; landmark roles; `aria-live` regions for toasts and verification results; focus moves to the page heading after route change; status never conveyed by colour alone; reduced-motion honoured; touch targets ≥ 44px.

## 12. Session UX
Activity (clicks, keys, API calls) resets the timer. At 13 minutes the modal shows a 2:00 countdown. "Stay signed in" calls the session-ping endpoint. At 15 minutes the app clears client state and goes to `/session-expired` with the message "You were signed out due to inactivity."
