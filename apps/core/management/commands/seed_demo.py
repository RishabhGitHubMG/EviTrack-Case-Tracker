import hashlib
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.cases.models import Case, CaseAssignment, Party
from apps.custody.models import CustodyEvent
from apps.custody.services import accept_transfer, reject_transfer, request_transfer
from apps.evidence.models import Evidence
from apps.evidence.tasks import verify_case_evidence_task
from apps.hearings.models import Hearing, Task
from apps.notifications.models import Notification
from apps.notifications.services import create_notification

DOMAIN = 'demo.evitrack.test'
PASSWORD = 'Demo#Pass2026'
TAMPERED_FILENAME = 'access.csv'

USERS = [
    ('admin', 'Ada', 'Admin', User.Role.ADMIN, True),
    ('manager', 'Morgan', 'Manager', User.Role.CASE_MANAGER, True),
    ('investigator', 'Ivan', 'Investigator', User.Role.INVESTIGATOR, True),
    ('custodian', 'Cora', 'Custodian', User.Role.CUSTODIAN, True),
    ('reviewer', 'Riley', 'Reviewer', User.Role.REVIEWER, True),
    ('pending', 'Pat', 'Pending', User.Role.INVESTIGATOR, False),
]

# Custody actions applied to evidence by filename, using the real services.
TRANSFERS = {
    'cctv_export.txt': 'pending',
    'statement.txt': 'accepted',
    'schedule.csv': 'rejected',
    'licence.txt': 'accepted',
    'ledger.csv': 'accepted',
}

CASES = [
    {
        'title': 'State v. Harlan - armed robbery',
        'case_type': Case.CaseType.CRIMINAL,
        'status': Case.Status.UNDER_INVESTIGATION,
        'priority': Case.Priority.CRITICAL,
        'parties': [('Dana Brooks', Party.PartyType.COMPLAINANT), ('Victor Hale', Party.PartyType.ACCUSED),
                    ('Sam Ortiz', Party.PartyType.WITNESS)],
        'assignees': [('investigator', CaseAssignment.RoleOnCase.LEAD), ('custodian', CaseAssignment.RoleOnCase.MEMBER),
                      ('reviewer', CaseAssignment.RoleOnCase.OBSERVER)],
        'evidence': [('CCTV export 14:00-14:30', 'cctv_export.txt'), ('Witness statement transcript', 'statement.txt')],
        'hearings': [(-21, 'Central Criminal Court, Room 4', 'Bail review', 'Bail denied; conditions reviewed.'),
                     (9, 'Central Criminal Court, Room 4', 'Pre-trial conference', '')],
        'tasks': [('Obtain CCTV vendor affidavit', -3, Task.Status.PENDING, 'investigator'),
                  ('Interview store manager', 4, Task.Status.IN_PROGRESS, 'investigator')],
    },
    {
        'title': 'Reyes family - parenting arrangements',
        'case_type': Case.CaseType.FAMILY,
        'status': Case.Status.OPEN,
        'priority': Case.Priority.HIGH,
        'parties': [('Nadia Reyes', Party.PartyType.CLIENT), ('Tom Reyes', Party.PartyType.OPPOSING_COUNSEL)],
        'assignees': [('investigator', CaseAssignment.RoleOnCase.LEAD), ('custodian', CaseAssignment.RoleOnCase.MEMBER)],
        'evidence': [('Text message export', 'messages.txt'), ('Parenting schedule log', 'schedule.csv')],
        'hearings': [(-40, 'Family Court 2', 'Initial directions', 'Interim schedule agreed.'),
                     (14, 'Family Court 2', 'Contested hearing', '')],
        'tasks': [('Collect message export certificate', 2, Task.Status.PENDING, 'investigator'),
                  ('Draft parenting plan', 10, Task.Status.PENDING, 'investigator')],
    },
    {
        'title': 'Acme v. Vector Labs - source code theft',
        'case_type': Case.CaseType.CIVIL,
        'status': Case.Status.IN_COURT,
        'priority': Case.Priority.MEDIUM,
        'parties': [('Acme Corp', Party.PartyType.COMPLAINANT), ('Vector Labs LLP', Party.PartyType.OTHER)],
        'assignees': [('investigator', CaseAssignment.RoleOnCase.LEAD), ('custodian', CaseAssignment.RoleOnCase.MEMBER)],
        'evidence': [('Repository commit log', 'commits.txt'), ('Licence agreement scan', 'licence.txt')],
        'hearings': [(-7, 'Commercial Court 3', 'Injunction hearing', 'Injunction granted in part.'),
                     (3, 'Commercial Court 3', 'Trial day 1', '')],
        'tasks': [('Prepare exhibit bundle', 1, Task.Status.IN_PROGRESS, 'investigator'),
                  ('File witness list', 6, Task.Status.PENDING, 'investigator')],
    },
    {
        'title': 'Riverside boundary dispute',
        'case_type': Case.CaseType.PROPERTY,
        'status': Case.Status.OPEN,
        'priority': Case.Priority.LOW,
        'parties': [('Gail Park', Party.PartyType.CLIENT), ('Elm Developments', Party.PartyType.OTHER)],
        'assignees': [('investigator', CaseAssignment.RoleOnCase.LEAD)],
        'evidence': [('Survey plan notes', 'survey.txt'), ('Boundary photo index', 'photos.csv')],
        'hearings': [(25, 'County Land Tribunal', 'Site visit and hearing', '')],
        'tasks': [('Confirm surveyor availability', 5, Task.Status.PENDING, 'investigator')],
    },
    {
        'title': 'Northwind phishing ring',
        'case_type': Case.CaseType.CYBERCRIME,
        'status': Case.Status.UNDER_INVESTIGATION,
        'priority': Case.Priority.HIGH,
        'parties': [('Unknown operator (alias K9)', Party.PartyType.ACCUSED),
                    ('Northwind Bank', Party.PartyType.COMPLAINANT)],
        'assignees': [('investigator', CaseAssignment.RoleOnCase.LEAD), ('reviewer', CaseAssignment.RoleOnCase.OBSERVER)],
        'evidence': [('Phishing email headers', 'headers.txt'), ('Server access log', TAMPERED_FILENAME)],
        'hearings': [(-12, 'Cyber Division Court', 'Preliminary hearing', 'Warrant for hosting records requested.'),
                     (18, 'Cyber Division Court', 'Warrant review', '')],
        'tasks': [('Verify access log hash chain', 0, Task.Status.IN_PROGRESS, 'investigator')],
    },
    {
        'title': 'Pike warehouse fraud',
        'case_type': Case.CaseType.CRIMINAL,
        'status': Case.Status.OPEN,
        'priority': Case.Priority.HIGH,
        'parties': [('Ledger Co Ltd', Party.PartyType.COMPLAINANT), ('Jonas Pike', Party.PartyType.ACCUSED),
                    ('Hana Lee', Party.PartyType.WITNESS)],
        'assignees': [('investigator', CaseAssignment.RoleOnCase.LEAD), ('custodian', CaseAssignment.RoleOnCase.MEMBER)],
        'evidence': [('Bank transfer ledger', 'ledger.csv'), ('Supplier invoice batch', 'invoices.txt')],
        'hearings': [(-2, 'Crown Court 1', 'Plea hearing', 'Not guilty plea entered.'),
                     (30, 'Crown Court 1', 'Case management', '')],
        'tasks': [('Reconcile invoice batch', 3, Task.Status.PENDING, 'investigator'),
                  ('Chain-of-custody review for ledger', -10, Task.Status.COMPLETED, 'investigator')],
    },
    {
        'title': 'Walsh collision claim',
        'case_type': Case.CaseType.CIVIL,
        'status': Case.Status.CLOSED,
        'priority': Case.Priority.LOW,
        'parties': [('Owen Walsh', Party.PartyType.CLIENT), ('Metro Transit', Party.PartyType.OTHER)],
        'assignees': [('investigator', CaseAssignment.RoleOnCase.LEAD)],
        'evidence': [('Accident report', 'report.txt'), ('Repair estimate', 'estimate.txt')],
        'hearings': [(-60, 'District Court 9', 'Settlement hearing', 'Settled; order filed.')],
        'tasks': [('Archive closing bundle', -30, Task.Status.COMPLETED, 'investigator')],
    },
    {
        'title': 'Municipal records review',
        'case_type': Case.CaseType.OTHER,
        'status': Case.Status.ARCHIVED,
        'priority': Case.Priority.LOW,
        'parties': [('City Archive', Party.PartyType.OTHER)],
        'assignees': [('investigator', CaseAssignment.RoleOnCase.LEAD)],
        'evidence': [('Archive index', 'index.csv'), ('Scanned council minutes', 'minutes.txt')],
        'hearings': [(-120, 'Administrative Panel', 'Records review', 'Records sealed for archive.')],
        'tasks': [('Confirm retention schedule', -90, Task.Status.COMPLETED, 'investigator')],
    },
]


class Command(BaseCommand):
    help = 'Seed EviTrack with synthetic demo users, cases, evidence, custody, hearings and tasks.'

    @transaction.atomic
    def handle(self, *args, **options):
        if User.objects.filter(email=f'manager@{DOMAIN}').exists():
            self.stdout.write('Demo data already exists. Use a fresh database to re-seed.')
            self._print_credentials()
            return

        users = self._create_users()
        evidence_root = Path(settings.EVIDENCE_ROOT)
        tampered = None

        for spec in CASES:
            case = self._create_case(spec, users)
            self._create_parties(case, spec['parties'])
            self._create_hearings_and_tasks(case, spec, users)
            for title, filename in spec['evidence']:
                evidence = self._create_evidence(case, title, filename, users, evidence_root)
                if filename == TAMPERED_FILENAME:
                    tampered = (case, evidence)

        self._tamper_and_verify(*tampered, users['admin'], evidence_root)
        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(CASES)} cases, {Evidence.objects.count()} evidence files, '
            f'{CustodyEvent.objects.count()} custody events, {Hearing.objects.count()} hearings, '
            f'{Task.objects.count()} tasks, {Notification.objects.count()} notifications.'
        ))
        self._print_credentials()

    def _create_users(self) -> dict[str, User]:
        users = {}
        for key, first, last, role, approved in USERS:
            users[key] = User.objects.create_user(
                email=f'{key}@{DOMAIN}',
                password=PASSWORD,
                first_name=first,
                last_name=last,
                role=role,
                is_approved=approved,
            )
        return users

    def _create_case(self, spec: dict, users: dict[str, User]) -> Case:
        manager = users['manager']
        closed = spec['status'] in (Case.Status.CLOSED, Case.Status.ARCHIVED)
        case = Case.objects.create(
            title=spec['title'],
            case_type=spec['case_type'],
            status=spec['status'],
            priority=spec['priority'],
            description=f'Synthetic demo case: {spec["title"]}.',
            closed_on=timezone.now().date() if closed else None,
            created_by=manager,
        )
        for key, role_on_case in spec['assignees']:
            CaseAssignment.objects.create(case=case, user=users[key], role_on_case=role_on_case)
        return case

    def _create_parties(self, case: Case, parties: list) -> None:
        for name, party_type in parties:
            Party.objects.create(case=case, name=name, party_type=party_type)

    def _create_hearings_and_tasks(self, case: Case, spec: dict, users: dict[str, User]) -> None:
        now = timezone.now()
        for days, court, purpose, outcome in spec['hearings']:
            hearing_date = now + timedelta(days=days)
            hearing = Hearing.objects.create(
                case=case, hearing_date=hearing_date, court=court, purpose=purpose,
                outcome=outcome, created_by=users['manager'],
            )
            if days > 0:
                create_notification(
                    user=users['investigator'],
                    message=f'Upcoming hearing in {days} days: {purpose} ({case.case_no}, {court}).',
                    link=reverse('hearings:hearing_detail', kwargs={'pk': hearing.pk}),
                    notification_type=Notification.NotificationType.INFO,
                )

        for title, days, status, assignee_key in spec['tasks']:
            Task.objects.create(
                case=case, title=title, due_date=now + timedelta(days=days),
                status=status, assigned_to=users[assignee_key], created_by=users['manager'],
                completed_at=now if status == Task.Status.COMPLETED else None,
            )

    def _create_evidence(self, case: Case, title: str, filename: str, users: dict[str, User], root: Path) -> Evidence:
        investigator = users['investigator']
        lines = [title, 'Synthetic demo record for EviTrack. Not real evidence.']
        lines += [f'Entry {n}: sample value {n * 7}' for n in range(1, 6)]
        content = ('\n'.join(lines) + '\n').encode()

        relative = f'case_{case.case_no}/{filename}'
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

        evidence = Evidence.objects.create(
            case=case,
            title=title,
            description='Synthetic demo evidence.',
            file_path=relative,
            original_filename=filename,
            mime_type='text/csv' if filename.endswith('.csv') else 'text/plain',
            file_size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            uploaded_by=investigator,
            current_holder=investigator,
        )

        now = timezone.now()
        CustodyEvent.objects.create(
            evidence=evidence,
            from_user=None,
            to_user=investigator,
            status=CustodyEvent.Status.ACCEPTED,
            reason='Initial intake, verification, and cryptographic vault deposit.',
            resolved_at=now,
            resolved_by=investigator,
        )

        action = TRANSFERS.get(filename)
        if action:
            self._apply_transfer(evidence, action, users)
        return evidence

    def _apply_transfer(self, evidence: Evidence, action: str, users: dict[str, User]) -> None:
        investigator, custodian = users['investigator'], users['custodian']
        event = request_transfer(
            evidence=evidence,
            from_user=investigator,
            to_user=custodian,
            reason=f'Lab examination for {evidence.case.case_no}.',
        )
        if action == 'accepted':
            accept_transfer(custody_event=event, user=custodian)
        elif action == 'rejected':
            reject_transfer(
                custody_event=event, user=custodian, reason='Evidence seal was not intact on arrival.',
            )

    def _tamper_and_verify(self, case: Case, evidence: Evidence, admin: User, root: Path) -> None:
        (root / evidence.file_path).write_bytes(b'altered after intake\n')
        verify_case_evidence_task(case.pk, admin.pk)

    def _print_credentials(self) -> None:
        self.stdout.write('')
        self.stdout.write('Demo sign-in (password for all accounts: ' + PASSWORD + ')')
        for key, _first, _last, role, approved in USERS:
            status = '' if approved else '  [pending approval, cannot sign in]'
            self.stdout.write(f'  {role:<14} {key}@{DOMAIN}{status}')
