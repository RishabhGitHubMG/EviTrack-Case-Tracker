# EviTrack – Digital Evidence & Case Tracker

<p align="center">
  <strong>🔒 Secure Case Management & Evidence Integrity for Law Enforcement & Legal Professionals</strong>
</p>

---

## Overview

**EviTrack** is a production-quality web application designed for small law firms and local police stations to securely manage cases, digital evidence, hearings, and tasks — replacing paper registers, spreadsheets, and chat groups with one unified system.

### Key Features

- **Case Management** – Full lifecycle tracking with state machine transitions (Open → Under Investigation → In Court → Closed → Archived)
- **Evidence Vault** – SHA-256 integrity verification, versioning, drag-and-drop upload, QR labels
- **Chain of Custody** – Two-party handshake protocol (Request → Accept/Reject) with complete audit trail
- **Hearing Calendar** – FullCalendar integration with automated reminders (7d, 1d, 2h before)
- **Task Management** – Assignments, deadlines, overdue detection, filing deadline tracking
- **Role-Based Access Control** – 5 roles: Admin, Case Manager, Investigator, Evidence Custodian, Read-only Reviewer
- **Immutable Audit Log** – Cryptographic hash-chaining, tamper-evident, append-only log
- **2FA Authentication** – TOTP-based two-factor with QR code setup
- **Session Security** – 15-minute idle timeout, django-axes brute-force lockout
- **PDF Reports** – WeasyPrint-generated case summaries, evidence manifests, custody chains
- **Dark/Light Mode** – Premium UI with Bootstrap 5, Inter font, navy/amber color scheme

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.1, Django REST Framework |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Task Queue | Celery + Redis |
| Frontend | Bootstrap 5, FullCalendar 6, vanilla JS |
| Auth Security | Argon2 + bcrypt, TOTP 2FA, django-axes |
| Evidence Integrity | SHA-256 hashing, hash-chained audit log |
| PDF Generation | WeasyPrint |
| Deployment | Docker, Gunicorn, Nginx |

## Quick Start

### Prerequisites

- Python 3.11+
- Redis (for Celery, optional in dev)

### Installation

```bash
# Clone the repository
git clone https://github.com/RishabhGitHubMG/EviTrack-Case-Tracker.git
cd EviTrack-Case-Tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements/dev.txt

# Copy environment config
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed demo data (optional)
python manage.py seed_demo

# Start development server
python manage.py runserver
```

Visit `http://localhost:8000` to access EviTrack.

### Demo Credentials (after seed_demo)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@evitrack.local | EviTrack@2026 |
| Case Manager | manager@evitrack.local | EviTrack@2026 |
| Investigator | investigator@evitrack.local | EviTrack@2026 |
| Custodian | custodian@evitrack.local | EviTrack@2026 |
| Reviewer | reviewer@evitrack.local | EviTrack@2026 |

## Project Structure

```
evitrack/
├── apps/
│   ├── accounts/     # User auth, roles, 2FA, admin approval
│   ├── cases/        # Case CRUD, parties, state transitions
│   ├── evidence/     # Evidence vault, SHA-256, versioning
│   ├── custody/      # Chain of custody handshake
│   ├── hearings/     # Hearings, tasks, calendar
│   ├── notifications/# Reminders, in-app notifications
│   ├── reports/      # PDF report generation
│   ├── audit/        # Immutable audit log with hash chaining
│   └── core/         # Dashboard, search, utilities
├── evitrack/         # Project settings, URLs, WSGI, Celery
├── templates/        # Django templates
├── static/           # CSS, JS assets
├── requirements/     # pip dependency files
└── manage.py
```

## User Roles & Permissions

| Permission | Admin | Case Manager | Investigator | Custodian | Reviewer |
|-----------|-------|-------------|-------------|-----------|----------|
| Manage users | ✅ | ❌ | ❌ | ❌ | ❌ |
| Create cases | ✅ | ✅ | ❌ | ❌ | ❌ |
| Edit cases | ✅ | ✅ | ✅* | ❌ | ❌ |
| Upload evidence | ✅ | ✅ | ✅ | ✅ | ❌ |
| Transfer custody | ✅ | ✅ | ✅ | ✅ | ❌ |
| View assigned cases | ✅ | ✅ | ✅ | ✅ | ✅ |
| Generate reports | ✅ | ✅ | ❌ | ❌ | ❌ |

*Investigators can edit cases they are assigned to.

## Security Features

- **Argon2 + bcrypt** password hashing
- **TOTP 2FA** with QR code provisioning
- **Session timeout** (15-min idle with 2-min warning)
- **Brute-force lockout** (5 attempts, 30-min cooloff)
- **SHA-256 evidence integrity** verification
- **Cryptographic hash-chaining** in audit log
- **RBAC** with case-level access control
- **CSP headers** enforced in production
- **HTTPS-only** with HSTS in production

## License

This project is developed for educational and professional use.

---

<p align="center">
  Built with ❤️ using Django 5.1 | <strong>EviTrack</strong> – Where Evidence Meets Integrity
</p>
