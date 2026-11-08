# TODO – INDEX (replaces the old single TODO list)

Detailed items: `TODO_BACKEND.md` (BE-…) and `TODO_FRONTEND.md` (FE-…). Process: `WORKFLOW.md`. Status log: `PROGRESS.md`.
Update the table after every batch. A slice is **Done** only when its Definition of Done (WORKFLOW §3) is met.

## Current slice: S0

| Slice | Journey step | Backend | Frontend | Slice status |
|---|---|---|---|---|
| S0 | Foundations | 0/7 | 0/7 | Not started |
| S1 | Landing page | 0/1 | 0/6 | Not started |
| S2 | Register, Login, OTP, TOTP | 0/8 | 0/9 | Not started |
| S3 | App shell | 0/5 | 0/9 | Not started |
| S4 | Dashboard | 0/3 | 0/5 | Not started |
| S5 | Cases | 0/8 | 0/7 | Not started |
| S6 | Evidence | 0/9 | 0/7 | Not started |
| S7 | Custody | 0/5 | 0/6 | Not started |
| S8 | Hearings, tasks, calendar | 0/5 | 0/5 | Not started |
| S9 | Notifications and preferences | 0/4 | 0/4 | Not started |
| S10 | Reports and search | 0/4 | 0/3 | Not started |
| S11 | Admin and account | 0/8 | 0/6 | Not started |
| S12 | Hardening and cutover | 0/7 | 0/8 | Not started |

## Carried over from the Django-template phase (do not lose)
- [ ] Docker image build (no daemon in the agent sandbox): user verifies with `docker compose up --build`
- [ ] PostgreSQL audit-trigger rejection probe (blocked in sandbox): user verifies on their machine
- [ ] Live Redis + Celery worker + Beat reminder run: user verifies on their machine
- [ ] Real-browser review of PDF layouts (samples to `docs/samples/`)
- [ ] Browser-test of legacy pages is superseded by the React rebuild; keep legacy tests green until S12

## Later documents (generate from real code after S12)
- [ ] `docs/ARCHITECTURE.md` · `docs/DEMO_SCRIPT.md` · `docs/TESTING.md` · `docs/VIVA_QA.md`

## Notes
- Move old docs to `docs/archive/` (old `FRONTEND.md`, old TODO items already completed). Keep `PROGRESS.md`'s history.
