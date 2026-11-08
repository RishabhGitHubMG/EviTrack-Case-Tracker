# EviTrack – WORKFLOW (how the AI builds, slice by slice)

Backend and frontend are built **together, one user-journey slice at a time**, in the order a real user meets the product. The Django template UI stays live until the final cutover (S12).

## 1. Slice order
| Slice | Journey step | What the user can do when it is done |
|---|---|---|
| S0 | Foundations | Frontend scaffold runs; API skeleton, schema and type generation work; design system exists |
| S1 | **Landing page** | Visitor understands the product and can click Sign in / Request access |
| S2 | **Register, Login, OTP, TOTP** | Visitor can request access, sign in with email code, sign out; pending/locked states work |
| S3 | **App shell** | Signed-in user gets sidebar, top bar, breadcrumbs, dark mode, bell and search stubs, session timeout, 403/404/500 |
| S4 | **Dashboard** | Role-aware KPIs, charts, attention lists |
| S5 | **Cases** | List, create/edit, detail with Overview, Parties, Assignments, Timeline, Audit; status flow |
| S6 | **Evidence** | List, upload with progress, detail, preview, download, verify, versions, integrity history |
| S7 | **Custody** | Timeline, request/accept/reject, inbox, QR label |
| S8 | **Hearings, tasks, calendar** | Calendar, hearing form and outcome flow, task list |
| S9 | **Notifications and preferences** | Bell dropdown, full centre, preferences, reminders visible |
| S10 | **Reports and search** | Reports page with five PDFs, global search and results page |
| S11 | **Admin and account** | Approvals, users and roles, audit viewer, failed logins, security settings, profile, change password, TOTP |
| S12 | **Hardening and cutover** | a11y and responsive pass, print, e2e crawl, Docker with SPA, README, legacy removal |

## 2. Loop inside every slice
1. **Plan (≤ 5 min):** read the slice items in `TODO_BACKEND.md`, `TODO_FRONTEND.md`, `API_CONTRACT.md`, and the matching sections of `UX.md` and `UI_SPEC.md` (grep headings).
2. **Backend:** serializers, thin views over existing services, permissions, tests; run schema generation; commit locally.
3. **Types:** `npm run api:types`.
4. **Frontend:** build components first (only the ones the slice needs), then pages with all states; wire hooks to the API.
5. **Tests:** pytest for the API; Vitest for components/forms; Playwright for the slice's journey at 1440px and 390px with the right roles; axe check.
6. **Fix** what the browser run reveals (overflow, console errors, contrast, keyboard).
7. **Docs and push:** tick TODO items, update `PROGRESS.md` and `API_CONTRACT.md`, `git status` + `git diff --stat` + grep key edits, commit, push.

## 3. Definition of Done (a slice is done only when all are true)
- [ ] Every API endpoint of the slice exists, matches `API_CONTRACT.md`, and has pytest tests for success, validation, 401, 403/404 and audit (where relevant).
- [ ] Full backend suite green (legacy tests included); `makemigrations --check` clean.
- [ ] Frontend `tsc --noEmit`, ESLint and Vitest green.
- [ ] Every page of the slice has loading, empty, error and success states and follows `UI_SPEC.md`.
- [ ] Role visibility matches `SPEC.md` §1 (tested with at least one allowed and one denied role).
- [ ] Playwright journey passes at 1440×900 and 390×844; no console errors; no horizontal overflow; axe has no serious/critical issues.
- [ ] Screenshots saved to `docs/screenshots/<slice>/`.
- [ ] TODO items ticked; `PROGRESS.md` updated; anything not verified is listed with a reason.
- [ ] Committed and pushed.

## 4. Rules of thumb
- Smallest working slice first, polish second, but never skip states.
- Build a component only when a page needs it; reuse before creating.
- Don't build ahead: no S6 code while S5 is open.
- If an endpoint turns out wrong, fix the contract file and the code together.
- Never fake data in the SPA; use the API and seeded demo data. MSW mocks are for unit tests only.
- When blocked by the environment, record "not verified: reason" and continue.

## 5. Batching guidance (tokens are scarce)
Do large batches: backend + frontend for a whole slice per session when possible. A session that ends after one small fix is a failure of planning. Update the TODO files every few items so a new account resumes exactly where the last stopped.

## 6. Where files go
```
AGENTS.md                      (repo root)
docs/SPEC.md  UX.md  UI_SPEC.md  FRONTEND.md  BACKEND.md  API_CONTRACT.md
docs/TODO.md (index)  TODO_FRONTEND.md  TODO_BACKEND.md  WORKFLOW.md  PROGRESS.md
docs/archive/                  (old notes; lowest priority)
docs/screenshots/<slice>/
frontend/                      (Vite app)
```
Later (generated from real code): `docs/ARCHITECTURE.md`, `docs/DEMO_SCRIPT.md`, `docs/TESTING.md`, `docs/VIVA_QA.md`.
