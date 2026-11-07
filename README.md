# EviTrack - Digital Evidence and Case Tracker

EviTrack is a Django web app for small law firms and police stations to track cases, digital evidence, chain of custody, hearings and tasks in one place. Every evidence file is hashed with SHA-256, every login needs a one-time email code, and every sensitive action is written to a hash-chained audit log.

## Status

- Automated tests: 118 passing (`python -m pytest`).
- Browser-tested in headless Chromium: email OTP login, dashboard, dark-mode save per user, 13-minute session warning, mobile sidebar drawer, and page loads for cases, evidence, profile, password change and calendar.
- Not yet verified live: the Docker image build and `docker compose up`, a live Celery Beat and worker run against Redis, the PostgreSQL audit-trigger rejection test, and real email delivery.

## Features

- **Cases**: create, edit, assign users, parties, status changes and a timeline.
- **Evidence vault**: upload, SHA-256 hashing, versions, verify, bulk verify, tags, QR labels and download/preview logging.
- **Chain of custody**: a transfer is requested, then accepted or rejected by the receiving person.
- **Hearings and tasks**: hearings, tasks with deadlines, and a calendar page.
- **Reminders**: Celery Beat sends due reminders by email, in-app and mock SMS, with retries and escalation.
- **Reports**: five case-scoped PDF reports generated with WeasyPrint.
- **Audit**: admin viewer, CSV export and a hash-chain verify action.
- **Search**: header search across cases, parties and evidence, limited to cases the user can access.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.1, Django REST Framework |
| Database | SQLite (local default), PostgreSQL (Docker and production) |
| Background jobs | Celery 5 with Celery Beat, Redis broker |
| Frontend | Bootstrap 5, FullCalendar, Chart.js, vanilla JavaScript |
| Auth | Email OTP on every login, optional authenticator app (TOTP), django-axes lockout, Argon2 hashing |
| Integrity | SHA-256 per file, hash-chained audit log, database trigger for audit updates and deletes (present on PostgreSQL; live rejection not yet verified) |
| PDF | WeasyPrint |
| Deployment | Docker Compose, Gunicorn, nginx |

## Setup without Docker

Requirements: Python 3.11 or newer. Redis is only needed for Celery.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Local development uses SQLite by default and the console email backend, so the sign-in code is printed in the `runserver` terminal.

`seed_demo` is idempotent: it stops if the demo manager already exists. To reseed, start from a fresh database.

To run background jobs, start Redis and then, in two more terminals:

```bash
redis-server
celery -A evitrack worker -l info
celery -A evitrack beat -l info
```

The development settings read `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` and default to `redis://localhost:6379/0`.

## Setup with Docker

Requirements: Docker with the Compose plugin (`docker compose version`).

```bash
cp .env.example .env
# Edit .env: set EVITRACK_SECRET_KEY and POSTGRES_PASSWORD
docker compose up -d --build
docker compose exec web python manage.py seed_demo
docker compose logs -f web         # sign-in codes are printed here unless SMTP is set
```

Open `http://localhost:8080/` (change with `HTTP_PORT` in `.env`).

Services: `db` (PostgreSQL 16), `redis`, `migrate` (runs once), `web` (Gunicorn), `worker` (Celery), `beat` (Celery Beat), and `nginx`. Evidence is stored in the `evidence_store` volume at `/srv/evidence`, which only the app containers can write to. nginx serves evidence only through an internal location that Django authorises with `X-Accel-Redirect`.

Note: the Docker image build has not been run in this environment. Only `docker compose config` was validated.

## Environment variables

Copy `.env.example` to `.env`. The main variables:

| Variable | Purpose |
|----------|---------|
| `EVITRACK_SECRET_KEY` | Django secret key. Required in production. |
| `ALLOWED_HOSTS` | Comma-separated host names. |
| `DATABASE_URL` | PostgreSQL URL, for example `postgres://user:pass@host:5432/evitrack`. |
| `POSTGRES_PASSWORD` | Password for the Compose PostgreSQL service. |
| `REDIS_URL`, `EVITRACK_CACHE_URL` | Redis for rate limits and cache in production. |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Celery broker and results. |
| `EVIDENCE_ROOT` | Directory for evidence files. Keep it outside any public web root. |
| `EVIDENCE_USE_X_ACCEL` | `True` makes Django hand file delivery to nginx. |
| `SECURE_SSL_REDIRECT` | Keep `True` behind real TLS. Set `False` for plain-HTTP local Compose. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | SMTP settings. Without `EMAIL_HOST`, production prints email to the console. |
| `DEBUG`, `USE_SQLITE` | Development toggles (`DEBUG=1`, `USE_SQLITE=0` to use PostgreSQL locally). |

## Demo credentials

Created by `seed_demo`. All use password `Demo#Pass2026`.

| Role | Email |
|------|-------|
| Admin | admin@demo.evitrack.test |
| Case Manager | manager@demo.evitrack.test |
| Investigator | investigator@demo.evitrack.test |
| Custodian | custodian@demo.evitrack.test |
| Reviewer | reviewer@demo.evitrack.test |

`pending@demo.evitrack.test` exists but is awaiting approval and cannot sign in.

## Running tests

```bash
python -m pytest
python manage.py check
python manage.py makemigrations --check --dry-run
```

Production settings check (needs a real secret and host):

```bash
EVITRACK_SECRET_KEY=<long-random-value> ALLOWED_HOSTS=<your-host> \
  python manage.py check --deploy --settings=evitrack.settings.production
```

## WeasyPrint system libraries

WeasyPrint needs Pango and related libraries at runtime.

- **Debian or Ubuntu**: `sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0 libfontconfig1 libffi8 shared-mime-info fonts-dejavu-core`. The package names match the Dockerfile.
- **Windows**: install the GTK runtime that WeasyPrint's documentation recommends for Windows, then restart the terminal so its DLLs are on `PATH`. Report PDFs fail to render without it.

## Demo script (about 5 minutes)

1. **Sign in**: go to the sign-in page as `investigator@demo.evitrack.test`. Enter the password, then the six-digit code printed in the server log.
2. **Open a case**: from the dashboard, open a seeded case and review its parties, evidence and timeline.
3. **Upload evidence**: on the case, choose Upload evidence and add a small file. The file gets a SHA-256 hash and an evidence number.
4. **Verify**: open the evidence and press Verify. An untouched file shows as verified.
5. **Tamper**: a seeded file (`access.csv`) was altered after upload. Verify it to see the mismatch, which is recorded in the integrity history.
6. **Modified alert**: the case managers are notified in the app when verification fails. Email delivery depends on SMTP settings.
7. **Custody transfer**: from the evidence page, request a transfer to another user. Sign in as that user, then accept or reject it.
8. **Hearing reminder**: create a hearing with a date. Reminders are sent by Celery Beat, so start the worker and beat first. This step is not yet verified live.
9. **PDF report**: open Reports and download a case PDF. Each download is recorded in the audit log.

## Project structure

```
apps/
  accounts/       sign-in, email OTP, roles, approvals, profile, password change
  cases/          cases, parties, assignments, timeline
  evidence/       vault, hashing, versions, verification, download and preview
  custody/        transfer requests, accept and reject, QR label
  hearings/       hearings, tasks, calendar
  notifications/  reminders, in-app notifications, bell
  reports/        five case PDF reports
  audit/          audit log, hash-chain verify, CSV export
  core/           landing page, dashboard, search, error pages
evitrack/         settings (base, development, test, production), URLs, WSGI, Celery
templates/        Django templates
static/           CSS and JavaScript
requirements/     base.txt, dev.txt, prod.txt
nginx/            nginx config for Compose
docs/PROGRESS.md  build progress and decisions
Dockerfile, docker-compose.yml, .env.example
```

## Roles

- **Admin**: manages users and approvals, sees every case, and can view the audit log.
- **Case Manager**: creates cases and sees the cases they created or are assigned to. Only Case Managers and Admins can close or archive a case and assign users.
- **Investigator**, **Custodian**: work on assigned cases (upload evidence, request or accept custody transfers).
- **Reviewer**: read-only access to assigned cases.

## Future scope (not built)

- Integration with eCourts and CCTNS for case and hearing data.
- Certified forensic acquisition (imaging and write-blocking of source media). EviTrack hashes files it receives. It does not acquire devices.

## License

Developed for educational and professional use.
