from django.db import models
from academics.models import Session, Term
from schools.models import Branch

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


# class StudentAttendance(models.Model):
#     school = models.ForeignKey(SchoolRegistration, on_delete=models.CASCADE, related_name="student_attendance", null=True, blank=True)
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records", null=True, blank=True)
#     session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="student_attendance", null=True, blank=True)
#     term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="student_attendance", null=True, blank=True)
#     branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="student_attendance", null=True, blank=True)
#     classes = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="student_attendance", null=True, blank=True)
#     days_present = models.PositiveIntegerField(null=True, blank=True)
#     recorded_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name="recorded_attendance")
#     recorded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

#     class Meta:
#         unique_together = ('school', 'student', 'session', 'term', 'branch', 'classes')
#         indexes = [
#             models.Index(fields=['school', 'student', 'session', 'term', 'branch', 'classes']),
#         ]

#     def __str__(self):
#         return f"{self.student.full_name} - {self.days_present} days present in {self.session.session_name}"


# class ClassAttendance(models.Model):
#     school = models.ForeignKey(SchoolRegistration, on_delete=models.CASCADE, related_name="class_attendance", null=True, blank=True)
#     classes = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_attendance", null=True, blank=True)
#     session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="class_attendance", null=True, blank=True)
#     term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="class_attendance", null=True, blank=True)
#     branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="class_attendance", null=True, blank=True)
#     teacher = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="class_attendance", null=True, blank=True)
#     date = models.DateField(null=True, blank=True)

#     class Meta:
#         unique_together = ('school', 'classes', 'session', 'term', 'branch', 'date')
#         indexes = [
#             models.Index(fields=['school', 'classes', 'session', 'term', 'branch', 'date']),
#         ]

#     def __str__(self):
#         return f"{self.classes.name} attendance for {self.date} in {self.school.school_name}"
