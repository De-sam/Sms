from django.db import models
from datetime import timedelta, date
from landingpage.models import SchoolRegistration  # Import SchoolRegistration

class Session(models.Model):
    school = models.ForeignKey(
        SchoolRegistration,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_name = models.CharField(max_length=20, unique=True)  # e.g., "2023/24"
    start_date = models.DateField()  # The start date of the session
    end_date = models.DateField(editable=False)  # Automatically set, read-only
    is_active = models.BooleanField(default=False)  # Flag to mark whether this is the current active session

    class Meta:
        indexes = [
            models.Index(fields=['session_name']),  # Index for searching sessions by name
            models.Index(fields=['is_active']),     # Index for filtering active sessions
            models.Index(fields=['school']),        # Index for filtering sessions by school
        ]

    def save(self, *args, **kwargs):
        # Check if the object is being updated or created
        creating = not self.pk

        # If editing an existing session, check if the start date has changed
        if not creating:
            original_session = Session.objects.get(pk=self.pk)
            start_date_changed = original_session.start_date != self.start_date
        else:
            start_date_changed = True

        # Set the default end_date to be 9 months after the start_date if not provided
        # or if the start_date has been changed and the third term hasn't explicitly set the end date.
        if (not self.end_date) or (start_date_changed and not self.terms.filter(term_name='Third Term', end_date__isnull=False).exists()):
            self.end_date = self.start_date + timedelta(days=9 * 30)  # Roughly 9 months (30 days each)

        # Automatically set `is_active` based on the current date and session dates
        today = date.today()
        self.is_active = self.start_date <= today <= self.end_date

        super().save(*args, **kwargs)

        # Automatically create three terms for every new session
        if creating:
            Term.objects.create(session=self, term_name='First Term')
            Term.objects.create(session=self, term_name='Second Term')
            Term.objects.create(session=self, term_name='Third Term')

    def __str__(self):
        return self.session_name

# Term Model - Represents each of the three terms within a session
class Term(models.Model):
    TERM_CHOICES = [
        ('First Term', 'First Term'),
        ('Second Term', 'Second Term'),
        ('Third Term', 'Third Term'),
    ]

    term_name = models.CharField(max_length=20, choices=TERM_CHOICES)  # Term name
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='terms')  # Link term to a session
    start_date = models.DateField(null=True, blank=True)  # Initially optional, set later
    end_date = models.DateField(null=True, blank=True)    # Initially optional, set later

    class Meta:
        unique_together = ('term_name', 'session')  # Ensure that each term occurs only once per session
        indexes = [
            models.Index(fields=['term_name']),    # Index for faster filtering by term name
            models.Index(fields=['session']),      # Index for session term relationships
        ]

    def save(self, *args, **kwargs):
        # Save the term
        super().save(*args, **kwargs)

        # If it's the "Third Term" and end_date is set, update the session's end date
        if self.term_name == 'Third Term' and self.end_date:
            session = self.session
            session.end_date = self.end_date
            session.save(update_fields=['end_date'])

    def __str__(self):
        return f"{self.term_name} - {self.session.session_name}"
