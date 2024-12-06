from django.db import models
from academics.models import Session, Term
from schools.models import Branch
from students.models import Student
from classes.models import Subject, Class


class ResultStructure(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    classes = models.ManyToManyField(Class, blank=True)  # Optional field for classes
    ca_total = models.PositiveIntegerField(null=True, blank=True)  # Total CA marks
    exam_total = models.PositiveIntegerField(null=True, blank=True)  # Total exam marks
    conversion_total = models.PositiveIntegerField(null=True, blank=True)  # Marks to convert CA (e.g., 40)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.branch} - {self.term} ({self.ca_total} + {self.exam_total})"


class ResultComponent(models.Model):
    structure = models.ForeignKey(ResultStructure, on_delete=models.CASCADE, related_name='components', null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)  # Name of the component (e.g., "1st Test")
    max_marks = models.PositiveSmallIntegerField(null=True, blank=True)  # Maximum marks for this component
    order = models.PositiveSmallIntegerField(default=0, null=True, blank=True)  # Order of the component
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)  # Optional subject-specific component

    def __str__(self):
        subject_info = f" for {self.subject}" if self.subject else ""
        return f"{self.name} ({self.max_marks} marks){subject_info}"

class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    structure = models.ForeignKey(ResultStructure, on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='student_results', null=True, blank=True)
    ca_total = models.FloatField(null=True, blank=True)  # Computed total for CA
    exam_score = models.FloatField(null=True, blank=True)  # Score in exams
    total_score = models.FloatField(null=True, blank=True)  # Total score (CA + exams)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Result for {self.student} - {self.subject} ({self.structure.term})"


class StudentComponentScore(models.Model):
    result = models.ForeignKey(StudentResult, on_delete=models.CASCADE, related_name='component_scores', null=True, blank=True)
    component = models.ForeignKey(ResultComponent, on_delete=models.CASCADE, related_name='student_scores', null=True, blank=True)
    score = models.FloatField(null=True, blank=True)  # Actual score achieved in this component

    def __str__(self):
        return f"{self.result.student} - {self.component.name} ({self.score})"
