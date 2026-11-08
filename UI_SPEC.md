# EviTrack – UI/UX SPECIFICATION (page by page)

> Put this file at `docs/UI_SPEC.md`. It describes how every page and feature must look and behave.
> Feel: a calm, serious, trustworthy legal-tech product. Think "bank meets forensic lab", not "student project". Generous whitespace, strong hierarchy, no clutter, no gimmicks.

---

## 0. DESIGN SYSTEM (applies to every page)

### Colour tokens (CSS variables, light / dark)
| Token | Light | Dark | Use |
|---|---|---|---|
| --navy-900 | #14213D | #0B1426 | sidebar, headings, primary buttons |
| --navy-700 | #1B2A49 | #16233F | hover states, table headers |
| --amber-500 | #F2A900 | #F2A900 | accent, active nav marker, key highlights |
| --amber-600 | #E8A317 | #E8A317 | accent hover |
| --surface | #FFFFFF | #1A2540 | cards |
| --bg | #F5F7FA | #0F172A | page background |
| --border | #E2E8F0 | #2A3655 | dividers, card borders |
| --text | #1E293B | #E5E9F2 | body text (slate) |
| --muted | #64748B | #94A3B8 | secondary text |
| --success | #15803D | #4ADE80 | Verified, Completed, Accepted |
| --danger | #B91C1C | #F87171 | Modified, Overdue, Rejected, errors |
| --warning | #B45309 | #FBBF24 | Pending, Due soon |
| --info | #1D4ED8 | #60A5FA | Info, In Court |

All text/background pairs must meet WCAG AA (4.5:1). Never use colour alone to show status: always pair with an icon and a label.

### Typography
- Headings: **Source Serif 4** (600). Body and UI: **Inter** (400/500/600). Hashes, case numbers, evidence numbers: monospace (JetBrains Mono or system mono).
- Scale: page title 28px serif; section heading 20px serif; card title 16px Inter 600; body 14px; small/meta 12px; hash 12px mono.
- Line height 1.5 body, 1.25 headings. Max line length ~75 characters for reading text.

### Spacing, shape, depth
- 4px base unit; page padding 24px desktop, 16px mobile; card padding 20px; grid gap 16-24px.
- Radius: cards 12px, buttons and inputs 8px, pills 999px.
- Shadows: soft (0 1px 3px rgba(20,33,61,.08)); hover lift (0 6px 16px rgba(20,33,61,.12)). No heavy drop shadows.
- Transitions 150-200ms ease; respect `prefers-reduced-motion`.

### Core components
- **Buttons:** Primary = navy fill, white text; hover navy-700. Accent = amber fill, navy text (used once per page for the main call to action). Secondary = white with border. Danger = red outline, fills red on hover. Ghost = text only. Sizes sm/md/lg. Loading state shows a spinner and disables the button. Icons on the left (Lucide or Bootstrap Icons).
- **Inputs:** 40px height, 1px border, navy focus ring (2px, offset 2px) plus amber underline accent. Label above, helper text below, error text in red with an icon, shown inline on blur. Required fields marked with a red asterisk and `aria-required`.
- **Pills/badges:** rounded, tinted background + dark text + icon. Statuses: Open (info), Under Investigation (amber), In Court (indigo), Closed (grey), Archived (slate). Priority: Low (grey), Medium (blue), High (amber), Critical (red, bold).
- **Cards:** white surface, 1px border, soft shadow, optional header row (title left, actions right).
- **Tables:** sticky header in navy-700 with white text, zebra rows (very light), row hover tint, 48px rows, sortable headers with arrow icons, sticky first column on mobile scroll, pagination bottom-right with "Showing 1-20 of 134".
- **Modals:** centred, 520px, dimmed backdrop, focus trap, Esc to close, primary action right, cancel left.
- **Toasts:** top-right, 4s auto-dismiss, success/error/info icons, close button, `aria-live="polite"`.
- **Skeleton loaders:** grey shimmer blocks matching the final layout, shown for any data that loads by AJAX.
- **Empty states:** centred illustration (simple line icon), one-line explanation, one clear call-to-action button.
- **Confirm dialogs:** for irreversible actions (close case, reject transfer, delete task). State the consequence in plain words; the confirm button is red.
- **Hash badge:** monospace, shows first 8 + "…" + last 6 characters, copy icon button; clicking copies the full hash and shows a "Copied" toast.
- **Avatar:** circle with initials on navy, 32px (topbar) and 40px (lists).
- **Breadcrumbs:** under the top bar: Home / Cases / EVT-2026-0001 / Evidence.

### Dark mode
Toggle (sun/moon) in the top bar. Persisted per user on the server and applied before first paint (no flash). Charts, calendar, PDF previews and badges must all adapt.

### Responsive breakpoints
Mobile < 640px (sidebar becomes off-canvas drawer, tables scroll horizontally or collapse into cards, tabs become a scrollable strip); Tablet 640-1024px (sidebar collapsed to icons); Desktop > 1024px (full sidebar 260px). No horizontal page scroll at any width.

### Accessibility
Semantic landmarks (header, nav, main, footer), skip-to-content link, visible focus rings, full keyboard operation, ARIA labels on icon-only buttons, `aria-current="page"` on active nav, form errors linked with `aria-describedby`, modals with focus trap, minimum 44px touch targets on mobile, alt text on images.

---

## 1. APP SHELL (every logged-in page)

**Sidebar (left, 260px, navy-900, white text)**
- Top: EviTrack logo (shield + magnifier mark in amber) and wordmark in serif. Collapse button (chevron) shrinks it to a 72px icon rail with tooltips.
- Navigation groups with small uppercase labels:
  - *Workspace:* Dashboard, Cases, Evidence, Calendar, Tasks
  - *Custody:* My Custody Inbox (badge with pending count), Transfers
  - *Insights:* Reports, Search
  - *Administration* (admin and case managers only): Approvals (badge), Users and Roles, Audit Log, Failed Logins, Security Settings
- Active item: lighter navy background, 3px amber bar on the left, bold text. Hover: subtle lighten.
- Bottom: user card (avatar, name, role pill) opening the user menu.

**Top bar (64px, white/surface, bottom border)**
- Left: hamburger (mobile) and breadcrumbs.
- Centre: global search box (placeholder "Search cases, evidence, hashes…  /"). Pressing `/` focuses it. Typing shows a dropdown of grouped results (Cases, Parties, Evidence) with highlighted matches, arrow-key navigation, Enter to open, "See all results" link. Empty state: "No matches. Try a case number or hash prefix."
- Right: dark-mode toggle, notification bell with a red unread-count bubble, user menu (Profile, Change password, Notification preferences, Sign out).
- Bell dropdown: 5 latest notifications with icon, text, relative time ("2 h ago"), unread dot, "Mark all read" and "View all" links. Clicking one marks it read and opens its target.

**Page header (below breadcrumbs, on every page):** serif title on the left, one-line description in muted text, primary action button(s) on the right. Beneath it, optional tabs or filter bar.

**Footer:** small muted line: "EviTrack · Prototype with dummy data · v1.0". Not shown in the sidebar layout on mobile.

**Global behaviours:** toasts for every action result; the session-timeout modal appears after 13 minutes of inactivity ("You will be signed out in 2:00. Stay signed in?" with a live countdown, Stay signed in / Sign out); after 15 minutes the user is redirected to login with the message "You were signed out due to inactivity."

---

## 2. PUBLIC PAGES

### 2.1 Landing page (`/`)
- **Top nav:** logo left; links Features, How it works, Security; "Sign in" (secondary) and "Request access" (amber) on the right. Sticky with blur on scroll.
- **Hero:** deep navy gradient background with a faint grid pattern. Left: serif headline "Every case. Every file. Every handover. Proven." and a subtitle "One secure place for small law firms and police stations to manage cases, digital evidence, hearings and deadlines." Two buttons: Sign in (amber), See how it works (ghost, scrolls). Right: a product screenshot mock (case detail with a green Verified badge) floating at a slight angle with soft shadow.
- **Trust strip:** four icons with labels: SHA-256 integrity, Chain of custody, Role-based access, Immutable audit trail.
- **Problem and solution:** two columns. Left "Today" (paper registers, pen drives, chat groups, missed hearings) with muted red icons; right "With EviTrack" (central records, hashed evidence, automatic reminders) with green ticks.
- **Features grid (3x2 cards):** Case management, Evidence vault, Chain of custody, Hearings and reminders, Reports and dashboard, Audit and security. Each with icon, title, two-line description, hover lift.
- **How it works:** 3 numbered steps with connector line: 1 Upload and hash, 2 Transfer with a handshake, 3 Verify on demand. A small animated illustration of Verified turning to Modified.
- **Security section:** dark band with a checklist (email OTP, lockout, role-based case access, immutable logs, files outside web root).
- **Final call to action band:** "Ready to stop losing evidence?" with Sign in button.
- **Footer:** logo, short description, links, and a note that this is a prototype with dummy data.
- Animations: fade-up on scroll, subtle; no autoplay carousels.

### 2.2 Login (`/accounts/login/`)
Split-screen. Left (hidden on mobile): navy panel with logo, a one-line quote about evidence integrity, and a subtle pattern. Right: centred card (max 420px) with title "Sign in", fields Email and Password (show/hide eye toggle), "Forgot password?" is not required, a primary full-width "Continue" button. Under it: "New here? Request access". Errors appear in a red alert inside the card ("Incorrect email or password. 3 attempts left."). After 5 failures: amber alert "Account locked for 15 minutes." and the button is disabled with a visible countdown.

### 2.3 Email OTP (`/accounts/otp/`)
Same split layout. Card title "Check your email", text "We sent a 6-digit code to a***@demo.evitrack.test". Six separate digit boxes (auto-advance, paste support, numeric keypad on mobile). "Verify" button, "Resend code" link with a 30-second cooldown timer, "Back to sign in". Shows attempts remaining on errors; code expiry shown ("Expires in 9:42"). In development the helper text says "Development mode: the code is printed in the server console."

### 2.4 TOTP step (only for users with an authenticator)
Same card style: "Authenticator code", six digit boxes, helper text "Open your authenticator app", Verify button.

### 2.5 Register / Request access
Card with Full name, Email, Phone, Role requested (select), Password (strength meter bar: weak red, fair amber, strong green, with rule checklist: 12+ characters, upper, lower, number, symbol), Confirm password, a terms checkbox. On success, redirect to login with a green message "Request sent. An administrator will approve your account." Pending users who try to log in see a friendly amber panel "Your account is awaiting approval."

### 2.6 Error pages (403, 404, 500)
Centred, large serif code (403 / 404 / 500) in amber, a short human message, a primary "Back to dashboard" button (real link, not `javascript:`) and a secondary "Go to previous page". 403 says "You don't have access to this case or page." 404 "We couldn't find that page." 500 "Something went wrong on our side. The error has been recorded." (only claim recording if it truly is.)

---

## 3. DASHBOARD (`/dashboard/`)

Header: "Good morning, {first name}" (time-aware) and the role pill; right side: date and a "New case" accent button (hidden for read-only reviewers).

**KPI cards (row of 5, wraps to 2 columns on mobile):** Open cases, Hearings this week, Overdue tasks, Pending custody transfers, Integrity alerts. Each card: large number (serif 32px), label, small icon in a tinted circle, a tiny trend or helper line ("2 in the next 48 h"). Clicking a card opens the filtered list. Integrity alerts card is red-tinted when above zero; overdue tasks amber/red when above zero. Skeleton shimmer while loading.

**Charts (2x2 grid, Chart.js, theme-aware, rounded bars, soft gridlines, legends below, tooltips):**
1. Cases by status: doughnut with centre total.
2. Cases by type: horizontal bar.
3. Hearings per week: bar for the next 8 weeks.
4. Workload per user: stacked bar (cases and tasks), visible to managers and admins only.
5. Evidence uploads over time: line with area fill, last 12 weeks (full width).
Each chart card has a title, small "Last updated" text and an empty state ("No data yet").

**Lists (two columns):**
- *Upcoming hearings:* next 5, each with a date tile (month, day), case number and title, court, time and a "Reminder set" icon. Link "Open calendar".
- *Needs your attention:* pending custody transfers (Accept / Reject buttons inline), overdue tasks (red), failed integrity checks (red), unread notifications.
Reviewer role sees the same without action buttons. Admin additionally sees an "Awaiting approval" card.

---

## 4. CASES

### 4.1 Case list (`/cases/`)
Header: "Cases", description, "New case" accent button. Filter bar (card): search input, selects for Status, Priority, Type, Assignee, a "Clear filters" link, and a result count. Filters keep their values in the URL. Table columns: Case no. (monospace, link), Title, Type, Status pill, Priority pill, Assignees (avatar stack, +N), Next hearing (date), Updated. Sortable headers, 20 per page, pagination. Row click opens the case. Rows with a Critical priority get a thin red left border. Empty state: "No cases match your filters" with Clear filters. Mobile: each row becomes a card (number and title on top, pills below).

### 4.2 Create / Edit case
Two-column form in cards: left "Case details" (Title, Type, Priority, Description with a simple rich-text or plain textarea and a character count, Opened on date); right "Assignment" (searchable multi-select of users with role pills, and the Case Manager select) and a "Status" card (edit only, showing only allowed next statuses). Sticky footer bar with Cancel and Save (primary); unsaved-changes warning on leave. Inline validation, field-level errors, success toast and redirect to the case.

### 4.3 Case detail (`/cases/<id>/`)
**Header card:** case number (mono, with copy icon), title in serif, pills for status and priority, meta row (type, opened date, created by, assignees avatars). Actions on the right: Edit, Change status (dropdown showing only valid transitions with a confirm dialog), Generate report (dropdown with the five PDFs), more menu (Assign users, Close case; closing is manager/admin only and needs a confirm modal with a reason). A closed case shows a grey "Closed on …" banner and disables editing.

**Tab bar (sticky under the header, scrollable on mobile):** Overview, Parties, Evidence (count), Custody, Hearings (count), Tasks (count), Timeline, Audit. The active tab has an amber underline; the tab loads without losing scroll position and the URL reflects it (`?tab=evidence`).

- **Overview:** left, description and key facts; right, summary cards: evidence count, integrity status (all verified / N modified), next hearing countdown, open tasks, people assigned.
- **Parties:** table or cards: name, type pill (Complainant, Accused, Witness, Client, Opposing Counsel, Other), contact, notes, edit/delete icons. "Add party" opens a modal form.
- **Evidence:** grid of evidence cards (see 5.1) with upload button and a mini integrity summary bar ("8 verified, 1 modified, 2 never checked") and a "Verify all" button (starts a background job, shows a progress toast and updates results).
- **Custody:** list of all evidence items with current holder, status chip (In custody / Transfer pending) and a link to each timeline; pending transfers highlighted.
- **Hearings:** list and mini month view, "Schedule hearing" button, each hearing showing date, court, purpose, outcome pill, and next date.
- **Tasks:** list with checkbox-style status, assignee avatar, due date (red if overdue, amber if within 2 days), filing-deadline flag icon, "Add task" modal.
- **Timeline:** vertical timeline merging all events chronologically (case created, evidence uploaded, verified, transferred, hearing held, task completed, status changed). Each entry: coloured icon dot, title, actor, relative time with exact time on hover, and a link to the object. Filter chips by event type; "Load more".
- **Audit:** read-only table of audit entries for this case (who, action, object, IP, time), visible to managers and admins.

---

## 5. EVIDENCE

### 5.1 Evidence list (`/evidence/`) and evidence cards
Filter bar: search, case select, tags (multi-select chips), file type, integrity status, holder. Toggle between Grid and Table view. **Evidence card:** top area with a type icon or thumbnail (image preview, PDF icon, audio waveform icon, video icon); evidence number (mono) and title; case number link; tags as small chips; hash badge (short, copyable); integrity badge (green Verified with date, red Modified, grey Never verified); current holder avatar and name; version tag ("v3"); hover reveals quick actions (Open, Verify, Download). Empty state invites the first upload.

### 5.2 Upload (modal or page)
Large dashed drop zone ("Drag files here or browse") with accepted types and the size cap shown. Selected files appear as rows: file icon, name, size, a Title field, a Tags input, a progress bar (animated, percent), and a status (Uploading, Hashing, Done with the short SHA-256, or a red error such as "Double extensions are not allowed"). Option "This is a new version of…" (searchable select). Case is preselected when started from a case. Summary at the end: "4 files uploaded and hashed." with links.

### 5.3 Evidence detail (`/evidence/<id>/`)
**Header:** evidence number and title, case link, tags, version pill. Actions: Verify integrity (accent), Download, Upload new version, Request transfer, Print QR label.
**Left column (wide):** preview panel: image viewer with zoom, inline PDF viewer, audio/video player with controls, or a "Preview not available" panel with a download button. Below: tabs Details, Versions, Integrity history, Custody, Activity.
- *Details:* metadata table (original filename, MIME type, size, uploaded by/at, current holder, status, description), full SHA-256 in a mono block with a copy button and a short explanation tooltip ("a fingerprint of the file").
- *Versions:* vertical list v1…vN with hash, uploader, date, and "Current" badge; old versions are read-only and downloadable.
- *Integrity history:* table of checks (date, checked by, result pill, computed hash vs stored hash). Mismatch rows are red and show the two hashes side by side with the differing characters highlighted.
**Right column (sticky):** an **Integrity card**: large state icon and text. Green shield "Verified" with "Last checked 2 h ago by …", or red warning "Modified: file no longer matches its original fingerprint" with a "Notify case manager" confirmation. A big "Verify integrity now" button: on click it shows a spinner and "Re-computing hash…", then animates the result (green check pop, or red shake) and adds an entry to the history without reloading. Below: a compact **custody timeline**.

### 5.4 Verification result states
Verified: green banner, shield-check icon, toast "Integrity verified". Modified: red banner at the top of the page, red badge on every card and list for this file, a toast, an entry in the case manager's notifications, and a pinned "Integrity alert" on the dashboard until acknowledged by a manager.

---

## 6. CHAIN OF CUSTODY

### 6.1 Custody timeline (component, used on evidence detail and custody tab)
Vertical line with circular nodes: first node "Collected / Uploaded" (navy), then one node per transfer. Each node shows from → to (avatars), reason, time, and a status: Accepted (green check), Pending (amber clock, pulsing dot), Rejected (red cross with the reason). The current holder node is emphasised with a "Currently holding" amber tag.

### 6.2 Request transfer (modal)
Fields: Receiver (searchable select of case members only), Reason (required textarea), optional note. A stepper above shows "1 Request → 2 Receiver accepts → 3 Custody moves". Submit shows a toast and the node appears as Pending.

### 6.3 Custody inbox (`/custody/inbox/`)
Two tabs: *Incoming* and *Outgoing*. Incoming cards show the evidence (thumbnail, number, title), case, from-user, reason, time, hash badge, and Accept (green) / Reject (red outline, opens a modal that requires a reason). Accepting plays a brief success animation and moves custody. Outgoing shows status and a Cancel request link while pending. Empty state: "No pending transfers."

### 6.4 QR label (`/custody/<id>/label/`)
A printable card 90mm × 55mm preview on the page: QR code on the left, and on the right the evidence number (large mono), case number, short hash prefix, current holder, intake date. Buttons: Print, Download PNG, Download PDF. The QR opens the evidence detail page (login required). Print stylesheet hides all chrome and prints just the label.

---

## 7. CALENDAR, HEARINGS AND TASKS

### 7.1 Calendar (`/calendar/`)
FullCalendar styled with the design tokens. Toolbar: Prev/Next/Today, title, view switch (Month, Week, List). Left filter panel (collapsible): checkboxes for Hearings, Tasks, Filing deadlines, and a case select. Colours: hearings navy, tasks teal, filing deadlines amber, overdue red with an alert icon. Events show a short title; hover tooltip shows case, court and time; click opens a side drawer with details and Edit / Open case buttons. Clicking an empty day (users with edit rights) opens the "Schedule hearing" modal with the date prefilled. Drag to reschedule a hearing with a confirm toast and undo. Today is outlined in amber. Mobile defaults to List view.

### 7.2 Hearing form (modal or page)
Case (searchable), Date and time, Court, Purpose, Notes, and a "Reminders" section with chips for 7 days, 1 day, 2 hours (toggle each). After a hearing's date passes, the detail view offers **Record outcome**: Outcome (select + notes) and Next hearing date; on save an alert asks "Create the next hearing on 12 Mar?" with Create now / Not now.

### 7.3 Tasks (`/tasks/`)
Tabs: My tasks, All (managers), Overdue. List rows: checkbox, title, case link, assignee avatar, due date chip (red overdue, amber soon, grey later), filing-deadline flag. Quick status change inline; "New task" modal (title, case, assignee, due date, filing-deadline toggle, reminder toggles). Completed tasks fade and move to a collapsed "Completed" section.

---

## 8. NOTIFICATIONS

### 8.1 Notification centre (`/notifications/`)
Filter chips: All, Unread, Reminders, Custody, Integrity, System. Each notification row: coloured icon by type, bold text if unread, message, case/evidence link, relative time, and per-row "Mark read". Header buttons "Mark all read". Pagination. Empty state: "You're all caught up."
Reminder notifications read like "Hearing tomorrow 10:30, EVT-2026-0003, Pune District Court". Integrity notifications are red and pinned at the top until opened.

### 8.2 Notification preferences (`/accounts/preferences/`)
Cards: *Channels* (in-app always on, email toggle, SMS toggle with a phone field and a "mock" note in development) and *Reminder timing* (hearings: 7 d / 1 d / 2 h toggles; deadlines: 3 d / 1 d toggles). Save with a toast; "Send test notification" button.

---

## 9. REPORTS (`/reports/`)
Header "Reports". Left: a case picker (searchable). Right: five report cards with an icon, name, a one-line description, and Download PDF / Preview buttons: Case summary, Evidence register (with hashes), Custody history, Hearing schedule, Integrity report. Choosing a case enables the buttons; a spinner shows while generating and a toast confirms. A "Recent reports" table lists who generated what and when (from the audit log). **PDF look:** A4, navy header band with logo and report title in serif, case number and date range, clean tables with repeating header rows, hashes in mono that wrap and never overflow, page numbers "Page 2 of 4", and a footer "Generated by {name} on {date} · EviTrack". A grey "Prototype – dummy data" note.

---

## 10. SEARCH RESULTS (`/search/?q=`)
Large search input prefilled. Result groups with counts: Cases, Parties, Evidence. Each result shows the matched text highlighted, the case number, type and status pills, and a snippet. Tabs to filter by group, a note when the query looks like a hash ("Matched by SHA-256 prefix"). Only items the user may access appear. Empty state with tips ("Search by case number, party name, evidence title, tag or hash prefix").

---

## 11. ADMINISTRATION (admins; case managers see only what applies)

### 11.1 Approvals (`/accounts/approvals/`)
Table of pending registrations: name, email, phone, requested role, requested at; Approve (green) and Reject (red, with reason) buttons, plus a role select to assign the final role. Success toast and the row slides out. Badge count in the sidebar.

### 11.2 Users and roles (`/accounts/users/`)
Table with avatar, name, email, role pill, status (Active, Locked, Pending), last login; filters by role and status. Row actions: change role (modal), deactivate/reactivate, unlock, reset OTP/TOTP. Role pills use distinct colours (Admin navy, Case Manager amber, Investigator/Advocate blue, Evidence Custodian teal, Reviewer grey). A small legend explains what each role can do.

### 11.3 Audit log (`/audit/`)
Filter bar: user, action (select), case, date range, free-text. Table: timestamp, user, action pill, object (link), case, IP, expandable details row (JSON in a mono block). Buttons: Export CSV, **Verify audit chain** (runs the check; shows a green "Chain intact: 1,284 entries verified" or a red "Break detected at entry #412"). A banner explains "Entries are insert-only and cannot be edited or deleted."

### 11.4 Failed logins (`/audit/failed-logins/`)
Table: time, email tried, IP, user agent, attempt count, locked-out flag; "Unlock account" action; small chart of failures per day.

### 11.5 Security settings (`/security/`)
Read-mostly cards: session timeout (15 min), lockout policy (5 attempts / 15 min), OTP method, upload limits (size cap, allowed types), evidence storage location health (writable, free space), last audit-chain verification, last integrity sweep. A button "Run integrity sweep on all evidence".

---

## 12. ACCOUNT PAGES

- **Profile (`/accounts/profile/`):** avatar with initials, name, email (read-only), phone, role pill, last login, a TOTP card (enable with QR, disable with confirmation), recent activity list (last 10 audit entries for me).
- **Change password:** current, new (with the strength meter), confirm; success toast; other sessions are signed out.

---

## 13. STATES, FEEDBACK AND MICRO-INTERACTIONS (everywhere)
- Every list has a skeleton, empty and error state (error: red card with "Try again").
- Every form shows inline errors and a summary on top if more than two errors; the first invalid field is focused.
- Buttons show spinners during requests and never double-submit.
- Copy-to-clipboard always gives a toast.
- Destructive or irreversible actions always confirm.
- Success moments (Verified, transfer accepted) get a short, subtle animation; nothing flashy.
- Keyboard shortcuts: `/` search, `g d` dashboard, `g c` cases, `Esc` closes modals and drawers; a "?" opens a shortcut cheat sheet.
- Tooltips explain technical terms (SHA-256, chain of custody) in plain words.

## 14. ROLE VISIBILITY SUMMARY
| Area | Admin | Case Manager | Investigator/Advocate | Evidence Custodian | Reviewer |
|---|---|---|---|---|---|
| Dashboard | all data | own cases + workload | assigned cases | assigned cases + custody | assigned cases (read-only) |
| Create/edit case | yes | yes | edit if assigned | no | no |
| Assign users, close case | yes | yes | no | no | no |
| Upload evidence | yes | yes | yes | yes | no |
| Request/accept transfer | yes | yes | yes | yes | no |
| Verify integrity | yes | yes | yes | yes | yes (view result only) |
| Reports | all | own cases | assigned | assigned | assigned |
| Audit, users, security | yes | audit for own cases only | no | no | no |
Controls the user may not use are hidden, not just disabled; pages they may not open return the 403 page.

## 15. PRINT STYLES
Hide sidebar, top bar, buttons and filters. White background, black text, serif headings, page-break control so cards and table rows don't split, URL not appended to links, evidence QR label and case summary print cleanly on A4.
