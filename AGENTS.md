# AGENTS.md – rules for any AI agent working on EviTrack

EviTrack is a digital evidence and case tracker for small law firms and police stations (cases, SHA-256-verified evidence, chain of custody, hearings and reminders, role- and case-level access, immutable audit trail, dashboards, PDF reports).
Backend: Django 5 + DRF + Celery + PostgreSQL (already built, 118+ tests). Frontend: being rebuilt as a **Vite + React + TypeScript SPA** in `frontend/`, talking to a JSON API at `/api/v1`.

## 1. Source-of-truth precedence (when files disagree)
1. `docs/SPEC.md` – what the product must do (requirements, rules, roles).
2. `docs/UX.md` and `docs/UI_SPEC.md` – how it behaves and looks.
3. `docs/API_CONTRACT.md` – the frontend/backend agreement.
4. `docs/FRONTEND.md`, `docs/BACKEND.md` – how to build it.
5. `docs/TODO.md` (index) → `docs/TODO_FRONTEND.md`, `docs/TODO_BACKEND.md` – the tasks.
6. `docs/PROGRESS.md` – current status and decisions log.
Older notes (previous `docs/FRONTEND.md` inventory, Django-template notes) are archived in `docs/archive/` and lose to everything above.

## 2. Session start routine (keep it cheap; tokens are limited and can run out at any moment)
1. Read this file.
2. `git status` and `git log -3`.
3. Read `docs/TODO.md` and find the **current slice** (first slice that is not fully done).
4. Read ONLY that slice's sections in `TODO_BACKEND.md`, `TODO_FRONTEND.md` and `API_CONTRACT.md`. For other docs use grep on headings; do not read them whole.
5. Do not re-scan the repo. Targeted greps and reading specific files are fine.

## 3. How to work: vertical slices, backend and frontend together
Follow `docs/WORKFLOW.md`. For each slice, in order:
1. **Backend (small, first):** serializers, thin API views calling the existing service layer, permissions, pytest API tests, OpenAPI schema; regenerate the TypeScript types.
2. **Frontend:** pages, components, API hooks, all states (loading, empty, error, success), role visibility, responsive.
3. **Tests:** pytest (API + permissions), Vitest/RTL (components), Playwright e2e for the slice at 1440px and 390px with the right demo role(s).
4. **Docs:** tick items in the TODO files, update `docs/PROGRESS.md` (status, NEXT ACTION, session log), update `API_CONTRACT.md` if the contract changed.
5. **Commit and push** (see §5).
Do not start the next slice until the current slice's Definition of Done in `WORKFLOW.md` is met. If one item is blocked, record it and continue with the next independent item in the same slice.

## 4. Hard rules
- Keep the existing Django backend logic, models, migrations and tests working. The API layer wraps the service layer; never duplicate business logic in views, serializers or React.
- Legacy Django-template pages stay live and their tests keep passing until the final cutover slice (S12). Do not delete them earlier.
- Authorization is enforced in querysets and object permissions on the server. Hiding a button in React is never the only protection.
- Never mark an item done unless you ran it and it worked. Otherwise write "not verified" and why.
- Never log, return or display OTP codes in production behaviour. A dev/test-only mechanism (guarded by DEBUG/test settings) may expose them to Playwright.
- No real personal data anywhere. Demo data only (`seed_demo`).
- No new dependency without a one-line justification in `docs/PROGRESS.md` (Decisions).
- Don't change the spec silently. If something must change, edit the spec file and note it in `PROGRESS.md`.
- No questions to the user. Decide, record the decision, continue.

## 5. Git and testing
- Work on the current working branch; commit and push after every 3–5 completed items or at the end of a slice, whichever comes first. The user merges to `main`.
- Before each push: `git status`, `git diff --stat`, and grep to confirm key edits actually landed (earlier sessions had edits that did not persist).
- Run the full backend suite once per batch, frontend `tsc --noEmit` + Vitest once per batch, Playwright per slice.
- Migrations: add new ones; never edit applied ones.

## 6. Environment notes
- Headless Chromium via Playwright works here. Use it for visual and flow checks; save screenshots to `docs/screenshots/<slice>/`.
- If the dev server hangs, use the DevServerRestart tool immediately; do not diagnose.
- If a command is blocked by the environment, do not retry with a workaround. Record it as unverified in `TODO` and `PROGRESS.md` and move on. Known unverifiable here: Docker image build (no daemon), PostgreSQL audit-trigger rejection probe.
- Dev ports: Django `8000`, Vite `5173` (proxy `/api` → 8000).

## 7. Reporting format (end of every batch, max 4 lines)
`Done: <items>` · `Left in slice: <n>` · `Not verified: <items>` · `Next: <item>`
