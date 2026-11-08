# TODO – FRONTEND (Vite + React + TypeScript). Tick `[x]` only after running it. Add "(not verified: reason)" otherwise.

IDs: `FE-S<slice>-<n>`. Page visuals: `UI_SPEC.md` (section in brackets). Behaviour: `UX.md`. Every page needs loading, empty, error and success states. Archive the old `docs/FRONTEND.md` to `docs/archive/` first.

## S0 Foundations
- [x] FE-S0-01 (H) Scaffold `frontend/` with Vite + React + TS strict; ESLint (react-hooks, jsx-a11y), Prettier, Vitest + RTL, Playwright config, `.env.example`, npm scripts (dev, build, preview, test, e2e, lint, api:types)
- [x] FE-S0-02 (H) Tailwind + `styles/tokens.css` (all tokens, light/dark) + `globals.css` + `print.css`; self-hosted fonts (Inter, Source Serif 4, JetBrains Mono) [UI §0]
- [x] FE-S0-03 (H) Vite proxy `/api` and `/media-protected` → `localhost:8000` (`/api/v1/health/` returned 200 with `{"status":"ok"}`; `/media-protected/` reached Django and returned its expected root 404)
- [x] FE-S0-04 (H) `api/client.ts` (CSRF, credentials, error normalisation, 401 handling), query-key factory, QueryClient defaults, `api:types` generation wired
- [x] FE-S0-05 (H) Core `components/ui`: Button, Input, Textarea, Select, Checkbox, Switch, Card, Badge/Pill (status + priority variants), Skeleton, EmptyState, ErrorState, Tooltip, Toast, Dialog, ConfirmDialog, Dropdown, Tabs, Avatar, HashBadge + CopyButton, PasswordStrength, OtpInput
- [x] FE-S0-06 (M) Theme provider (class-based dark mode, no flash) and a `/design` dev-only route showing every component in light and dark (theme-before-bundle, persistence, and axe checks pass at desktop/mobile in both themes)
- [x] FE-S0-07 (M) Vitest tests for Button, Input error state, OtpInput, HashBadge copy; Playwright smoke config; GitHub-style `npm run check` (tsc + lint + test) (`npm run check` passes with 4 Vitest tests; Playwright smoke passes)

## S1 Landing page [UI §2.1]
- [x] FE-S1-01 (H) `PublicLayout`: sticky nav with blur, logo, Features/How it works/Security anchors, Sign in + Request access, mobile menu
- [x] FE-S1-02 (H) Hero with gradient + grid pattern, serif headline, subtitle, two CTAs, product mock (code-built, no external images)
- [x] FE-S1-03 (H) Trust strip (4 items), Problem vs Solution, Features grid (6 cards with hover lift)
- [x] FE-S1-04 (H) How it works (3 steps with connector and small Verified→Modified animation), Security band, final CTA, footer with prototype note
- [x] FE-S1-05 (M) Scroll fade-in (reduced-motion aware), smooth anchor scrolling, SEO tags (title, description, OG)
- [ ] FE-S1-06 (H) Playwright: J1 first half (landing renders, CTAs navigate), mobile 390px layout, axe check, Lighthouse a11y ≥ 95 (14 browser checks pass; axe reports no serious/critical violations; four light/dark screenshots saved; Lighthouse score not run)

## S2 Register, Login, OTP, TOTP [UI §2.2–2.5; UX J1, J2]
- [ ] FE-S2-01 (H) `AuthLayout` (split screen, hidden art on mobile)
- [ ] FE-S2-02 (H) Register page: zod schema, inline errors, strength meter, role select, terms, success → `/register/pending`
- [ ] FE-S2-03 (H) Pending-approval page and the amber "awaiting approval" state on login
- [ ] FE-S2-04 (H) Login page: show/hide password, attempts-left error, locked state with countdown, `?next=` support
- [ ] FE-S2-05 (H) OTP page: six boxes (auto-advance, paste, numeric keypad), expiry timer, resend with 30 s cooldown, attempts left, lock state; masked email
- [ ] FE-S2-06 (M) TOTP page (only when API says `totp_required`)
- [ ] FE-S2-07 (H) `AuthProvider`, `useSession`, `RequireAuth`, redirect rules (signed-in users away from `/login`), `/session-expired` page
- [ ] FE-S2-08 (H) Playwright: J1 register→pending; J2 login→OTP→dashboard placeholder; wrong password; 5 failures lock; wrong OTP; resend cooldown; axe; mobile
- [ ] FE-S2-09 (M) Vitest: login state machine, OTP input, error mapping

## S3 App shell [UI §1; UX §4, §12]
- [ ] FE-S3-01 (H) `AppShell`: sidebar (groups, active bar, badges, collapse to rail, mobile drawer), top bar, page header, breadcrumbs, footer note
- [ ] FE-S3-02 (H) Role-aware navigation from `can()` (hidden, not disabled); Reviewer read-only pill
- [ ] FE-S3-03 (H) Theme toggle persisted via `PATCH /me/preferences/`
- [ ] FE-S3-04 (H) NotificationBell with 60 s polling + focus refetch, dropdown, mark all read
- [ ] FE-S3-05 (H) Global search box with `/` shortcut, grouped suggest dropdown, arrow-key navigation, empty state
- [ ] FE-S3-06 (H) `SessionTimeout` modal (13 min warning, 2:00 countdown, Stay signed in / Sign out) and 15 min expiry
- [ ] FE-S3-07 (H) System pages: 403, 404, 500, session-expired (real links, honest wording)
- [ ] FE-S3-08 (M) Hotkeys (`g d`, `g c`, `?` cheat sheet), skip link, focus to heading on route change
- [ ] FE-S3-09 (H) Playwright: shell at 1440 and 390 (drawer opens/closes), theme persists after reload and per user, session modal via fake clock, role-based nav for all five roles, axe

## S4 Dashboard [UI §3]
- [ ] FE-S4-01 (H) KPI cards (5) with skeletons, clickable to filtered lists, red/amber tints
- [ ] FE-S4-02 (H) Chart wrappers (Doughnut, Bar, Line) themed from tokens; five charts with empty states; workload for A/M only
- [ ] FE-S4-03 (H) Upcoming hearings list (date tiles) and "Needs your attention" (transfers with inline Accept/Reject, overdue tasks, integrity alerts)
- [ ] FE-S4-04 (M) Greeting, role pill, "New case" button (hidden for Reviewer); Admin "Awaiting approval" card
- [ ] FE-S4-05 (H) Playwright: dashboard for admin, manager, investigator, reviewer; numbers match API; mobile layout; dark mode charts

## S5 Cases [UI §4]
- [ ] FE-S5-01 (H) Case list: filter bar (URL-synced), sortable table, pagination, priority left border, mobile cards, empty state
- [ ] FE-S5-02 (H) Case form (create/edit): two-column, assignment multi-select with user lookup, allowed-status select, sticky footer, unsaved-changes guard
- [ ] FE-S5-03 (H) Case detail header (pills, copy number, actions menu, closed banner) and URL-synced sticky tabs
- [ ] FE-S5-04 (H) Tabs: Overview, Parties (modal CRUD), Timeline (filter chips, load more), Audit (A,M)
- [ ] FE-S5-05 (H) Status change dropdown with confirm; Close case modal (reason)
- [ ] FE-S5-06 (M) Evidence, Custody, Hearings, Tasks tabs as shells linked to later slices (read-only lists first, filled in S6–S8)
- [ ] FE-S5-07 (H) Playwright: J3 first half; filters persist after refresh; unassigned case URL → 404 page; reviewer sees no edit controls; mobile

## S6 Evidence [UI §5]
- [ ] FE-S6-01 (H) Evidence list: grid and table toggle, filters, evidence cards with type icon/thumbnail, hash badge, integrity badge, holder, version
- [ ] FE-S6-02 (H) `FileDropzone` + upload rows (title, tags, per-file progress, hashing state, short SHA-256, error + retry, "new version of")
- [ ] FE-S6-03 (H) Evidence detail: header actions, preview panel (image zoom, PDF, audio, video, fallback), tabs Details, Versions, Integrity history
- [ ] FE-S6-04 (H) Integrity card with **Verify integrity** animation (Verified green pop / Modified red banner), history entry added without reload, side-by-side hash diff
- [ ] FE-S6-05 (M) "Verify all" in the case Evidence tab with progress via task polling
- [ ] FE-S6-06 (M) Dashboard integrity alert acknowledgement flow
- [ ] FE-S6-07 (H) Playwright: J3 second half and J5 (upload → verify → tamper file on disk → Modified → alert shown to manager); double-extension rejection; reviewer cannot upload; mobile

## S7 Custody [UI §6]
- [ ] FE-S7-01 (H) `Timeline` component and custody timeline on evidence detail
- [ ] FE-S7-02 (H) Request-transfer modal with stepper, receiver picker (case members only)
- [ ] FE-S7-03 (H) Custody inbox (Incoming/Outgoing tabs, Accept, Reject with reason, Cancel)
- [ ] FE-S7-04 (M) Case "Custody" tab
- [ ] FE-S7-05 (H) QR label page with print stylesheet, PNG and PDF downloads
- [ ] FE-S7-06 (H) Playwright: J4 with two roles in two browser contexts

## S8 Hearings, tasks, calendar [UI §7]
- [ ] FE-S8-01 (H) Calendar page with FullCalendar (month/week/list), token styling, filters, colour-coding, overdue icon, tooltip, event drawer
- [ ] FE-S8-02 (H) Hearing modal (create from day click, edit), reminder chips; drag-to-reschedule with undo toast
- [ ] FE-S8-03 (H) Record outcome + "create next hearing?" prompt
- [ ] FE-S8-04 (H) Tasks page (My tasks, All, Overdue), task modal, quick status toggle, completed section; case Hearings and Tasks tabs
- [ ] FE-S8-05 (H) Playwright: J6; scope (another user cannot see hearing); mobile defaults to List

## S9 Notifications and preferences [UI §8]
- [ ] FE-S9-01 (H) Notification centre with filter chips, unread styling, mark read / all, links, pagination
- [ ] FE-S9-02 (H) Preferences page: channels, reminder timing toggles, phone, test notification
- [ ] FE-S9-03 (M) Integrity notifications pinned/red; reminder text format
- [ ] FE-S9-04 (M) Playwright: reminders visible after seeding, bell updates, preference saved

## S10 Reports and search [UI §9, §10]
- [ ] FE-S10-01 (H) Reports page: case picker, five report cards, generate/download with spinner and toast, recent reports table (A,M)
- [ ] FE-S10-02 (H) Search results page: grouped tabs with counts, highlighted matches, hash-prefix note, empty state
- [ ] FE-S10-03 (M) Playwright: J8, download each PDF, search by hash prefix and party name as two users (scope)

## S11 Admin and account [UI §11, §12]
- [ ] FE-S11-01 (H) Approvals page (role select, approve/reject with reason, sidebar badge)
- [ ] FE-S11-02 (H) Users and roles page (filters, role change, deactivate, unlock, reset OTP, role legend)
- [ ] FE-S11-03 (H) Audit log page (filters, expandable details, CSV export, Verify chain result banner)
- [ ] FE-S11-04 (M) Failed logins page + chart; Security settings page + integrity sweep button
- [ ] FE-S11-05 (H) Profile page (TOTP enable with QR / disable, recent activity), Change password page (strength meter, success toast)
- [ ] FE-S11-06 (H) Playwright: J7; non-admin gets 403; manager sees only own-case audit

## S12 Hardening and cutover [UI §13–15; UX §10–11]
- [ ] FE-S12-01 (H) Responsive pass on every page at 390, 768, 1024, 1440; fix overflow, drawers, table-to-card behaviour
- [ ] FE-S12-02 (H) Accessibility pass: keyboard-only walkthrough of all journeys, focus order, aria-live regions, contrast in light and dark, axe clean
- [ ] FE-S12-03 (M) Print styles for case page, QR label and report-adjacent pages
- [ ] FE-S12-04 (M) Performance: code splitting verified, initial JS ≤ ~250 KB gzip, Lighthouse targets
- [ ] FE-S12-05 (H) Full e2e crawl (every route × role) with no console errors; all J1–J8 pass
- [ ] FE-S12-06 (H) Production build served by nginx/Django catch-all; CSP clean (no inline scripts); legacy UI removed per BACKEND §10
- [ ] FE-S12-07 (M) Screenshots of every main page (desktop + mobile, light + dark) in `docs/screenshots/final/`
- [ ] FE-S12-08 (M) README frontend section: setup, scripts, env, test commands, project structure
