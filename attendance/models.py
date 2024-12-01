from django.db import models
from academics.models import Session, Term
from schools.models import Branch
from classes.models import Class
from students.models import Student

class SchoolDaysOpen(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='days_open_records', null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='days_open_records', null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='days_open_records', null=True, blank=True)
    days_open = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('branch', 'session', 'term')  # Prevent multiple entries for the same branch, session, and term combination.
        indexes = [
            models.Index(fields=['branch', 'session', 'term']),  # Index for better query performance
        ]

    def __str__(self):
        return f"{self.branch.branch_name if self.branch else 'No Branch'} - {self.session.session_name if self.session else 'No Session'} - {self.term.term_name if self.term else 'No Term'}: {self.days_open if self.days_open is not None else 'No Days'} days"

class StudentAttendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendance_records', null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='attendance_records', null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='attendance_records', null=True, blank=True)
    student_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance_records', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records', null=True, blank=True)
    attendance_count = models.PositiveIntegerField(default=0, null=True, blank=True)  # The number of days the student attended
    date = models.DateField(auto_now_add=True, null=True, blank=True)  # Date of attendance entry
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('session', 'term', 'branch', 'student_class', 'student', 'date')  # Prevent multiple entries for the same student in the same class on the same date.
        indexes = [
            models.Index(fields=['session', 'term', 'branch', 'student_class', 'student', 'date']),  # Index for better query performance
        ]

    def __str__(self):
        return f"Attendance for {self.student.full_name()} - {self.session.session_name} - {self.term.term_name}: {self.attendance_count} days"


