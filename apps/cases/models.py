from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Case(models.Model):
    class CaseType(models.TextChoices):
        CRIMINAL = 'criminal', 'Criminal'
        CIVIL = 'civil', 'Civil'
        FAMILY = 'family', 'Family'
        PROPERTY = 'property', 'Property'
        CYBERCRIME = 'cybercrime', 'Cybercrime'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_INVESTIGATION = 'under_investigation', 'Under Investigation'
        IN_COURT = 'in_court', 'In Court'
        CLOSED = 'closed', 'Closed'
        ARCHIVED = 'archived', 'Archived'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    VALID_TRANSITIONS = {
        Status.OPEN: [Status.UNDER_INVESTIGATION, Status.IN_COURT],
        Status.UNDER_INVESTIGATION: [Status.IN_COURT, Status.CLOSED],
        Status.IN_COURT: [Status.CLOSED],
        Status.CLOSED: [Status.ARCHIVED],
        Status.ARCHIVED: [],
    }

    case_no = models.CharField(max_length=32, unique=True, blank=True)
    title = models.CharField(max_length=200)
    case_type = models.CharField(
        max_length=20, choices=CaseType.choices, default=CaseType.OTHER
    )
    status = models.CharField(
        max_length=25, choices=Status.choices, default=Status.OPEN
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    description = models.TextField()
    opened_on = models.DateField(auto_now_add=True)
    closed_on = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_cases',
    )

    class Meta:
        db_table = 'cases_case'
        ordering = ['-opened_on', '-id']
        verbose_name = 'Case'
        verbose_name_plural = 'Cases'
        indexes = [
            models.Index(fields=['case_no']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['opened_on']),
        ]

    def __str__(self) -> str:
        return f'{self.case_no} - {self.title}'

    def clean(self):
        super().clean()
        if self.pk:
            current_status = (
                Case.objects.filter(pk=self.pk)
                .values_list('status', flat=True)
                .first()
            )
            if current_status and current_status != self.status:
                allowed = self.VALID_TRANSITIONS.get(current_status, [])
                if self.status not in allowed:
                    current_label = self.Status(current_status).label
                    new_label = self.get_status_display()
                    allowed_labels = [self.Status(s).label for s in allowed]
                    allowed_str = ', '.join(allowed_labels) if allowed_labels else 'None (terminal state)'
                    raise ValidationError({
                        'status': (
                            f"Invalid status transition from '{current_label}' to '{new_label}'. "
                            f"Allowed transitions: {allowed_str}."
                        )
                    })

    def save(self, *args, **kwargs):
        if not self.case_no:
            year = timezone.now().year
            prefix = f"EVT-{year}-"
            last_case = (
                Case.objects.filter(case_no__startswith=prefix)
                .order_by('-case_no')
                .first()
            )
            if last_case and last_case.case_no:
                try:
                    last_seq = int(last_case.case_no.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            self.case_no = f"{prefix}{new_seq:04d}"

        if self.status in [self.Status.CLOSED, self.Status.ARCHIVED] and not self.closed_on:
            self.closed_on = timezone.now().date()

        super().save(*args, **kwargs)


class CaseAssignment(models.Model):
    class RoleOnCase(models.TextChoices):
        LEAD = 'lead', 'Lead'
        MEMBER = 'member', 'Member'
        OBSERVER = 'observer', 'Observer'

    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name='assignments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='case_assignments',
    )
    role_on_case = models.CharField(
        max_length=20,
        choices=RoleOnCase.choices,
        default=RoleOnCase.MEMBER,
    )
    assigned_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cases_assignment'
        verbose_name = 'Case Assignment'
        verbose_name_plural = 'Case Assignments'
        unique_together = ('case', 'user')
        constraints = [
            models.UniqueConstraint(
                fields=['case', 'user'], name='unique_case_user_assignment'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} - {self.case.case_no} ({self.get_role_on_case_display()})'


class Party(models.Model):
    class PartyType(models.TextChoices):
        COMPLAINANT = 'complainant', 'Complainant'
        ACCUSED = 'accused', 'Accused'
        WITNESS = 'witness', 'Witness'
        CLIENT = 'client', 'Client'
        OPPOSING_COUNSEL = 'opposing_counsel', 'Opposing Counsel'
        OTHER = 'other', 'Other'

    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name='parties'
    )
    name = models.CharField(max_length=200)
    party_type = models.CharField(
        max_length=20, choices=PartyType.choices, default=PartyType.OTHER
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'cases_party'
        verbose_name = 'Party'
        verbose_name_plural = 'Parties'
        indexes = [
            models.Index(fields=['case', 'party_type']),
        ]

    def __str__(self) -> str:
        return f'{self.name} ({self.get_party_type_display()}) - {self.case.case_no}'
