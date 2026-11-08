# EviTrack Remaining Work

Tasks are ordered by priority, then by dependency. A task is complete only after its verification succeeds; blocked checks stay marked not verified with the reason.

## Frontend screens
- [x] T1 — [High] Add notification preferences (reminder timing and channels), migration, scheduler integration, page, and tests. Note: targeted account/reminder tests passed (19); migration applied; Playwright browser check not verified because Playwright is unavailable in the environment.
- [x] T2 — [High] Add hearing create/edit actions from the calendar and verify both flows. Note: case-scoped schedule control and date-click prefill added; detail/edit route tests passed (5), including read-only reviewer restrictions; Playwright browser check not verified because Playwright is unavailable.
- [x] T3 — [High] Add read-state and notification-type filters; test them. Note: all/read/unread and type filters, combined filters, and invalid-value behavior pass notification tests (15).
- [ ] T4 — [High] Confirm and, if needed, fix the evidence-list tag filter; test filtered results. Note: pending.
- [ ] T5 — [High] Add a bulk-verify control to the case Evidence tab and verify the result. Note: pending.
- [ ] T6 — [High] Check and verify case assign/unassign controls and access behavior. Note: pending.
- [ ] T7 — [Medium] Check audit/admin screens and navigation, including approval queue, failed logins, security settings, and audit-chain verification. Note: pending.
- [ ] T8 — [Medium] Review remaining partial account and case screens for required actions, empty/error states, and route usability; fix and test confirmed gaps. Note: pending.
- [ ] T9 — [Medium] Verify the five PDF reports through the reports page and check the required case-picker/list behavior. Note: pending.
- [ ] T10 — [Medium] Verify search, custody timeline, dashboard charts, evidence upload/detail, and landing updates in the integrated UI. Note: pending.

## Design polish
- [ ] T11 — [Medium] Polish all pages for consistent typography, spacing, loading/error/empty states, accessible controls, keyboard use, and responsive tables; check contrast and print styles. Note: pending.

## Browser verification
- [ ] T12 — [High] Run Playwright at 1440px and 390px as an admin and a normal user; exercise primary flows and record failures. Note: pending.
- [ ] T13 — [High] Capture verified desktop/mobile screenshots in `docs/screenshots/` and record page, role, and viewport. Note: pending.
- [ ] T14 — [Medium] Crawl internal links/routes and check for dead links, placeholders, and server errors. Note: pending.

## Docker/Celery/PostgreSQL verification
- [ ] T15 — [High] Validate Docker build, Compose startup, and nginx configuration for the documented services. Note: pending.
- [ ] T16 — [High] Run a live Celery/Beat + Redis reminder scan and verify scheduled delivery/idempotency. Note: pending.
- [ ] T17 — [High] Verify PostgreSQL audit-trigger UPDATE/DELETE rejection; if the environment blocks the probe, retain “not verified” and record the reason without retrying. Note: pending.
- [ ] T18 — [Medium] Reconcile Docker, database, evidence-storage, and audit-immutability deployment claims with successful runtime checks. Note: pending.

## README
- [ ] T19 — [Medium] Verify README setup, environment variables, Docker, Celery, seed data, five-minute demo, project structure, and limitations against tested behavior; update inaccurate claims. Note: pending.

## Status reconciliation
- [ ] T20 — [High] Reconcile all remaining Foundation, Accounts, Cases, Evidence, Custody, Hearings, Notifications, Reports, Audit, Search, Security, Data, Tests, Deploy, and Docs rows in `docs/PROGRESS.md` against executed checks. Note: pending.
- [ ] T21 — [Medium] Reconcile every page, route, shell component, and gap in `docs/FRONTEND.md`; record browser results and update session logs. Note: pending.
- [ ] T22 — [Medium] Update completion measurement and NEXT ACTION/status header to match verified outcomes only. Note: pending.

## Final QA
- [ ] T23 — [High] Run the full test suite once per batch and resolve any regressions before marking work complete. Note: pending.
- [ ] T24 — [High] Run Django `check --deploy`, migration-drift check, and the route/dead-link crawl; record blocked checks as not verified with reasons. Note: pending.
- [ ] T25 — [High] Perform final cross-role desktop/mobile smoke checks, inspect git diff/status, and confirm all docs agree with observed results. Note: pending.
