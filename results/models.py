from django.db import models
from classes.models import Class, Subject
from schools.models import Branch
from students.models import Student  # Assuming you have a Student model
from academics.models import Session, Term
from classes.models import Class, Subject



class ResultStructure(models.Model):
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        related_name="result_structures", 
        null=True, 
        blank=True
    )
    ca_total = models.PositiveIntegerField(null=True, blank=True)  # Total CA marks
    exam_total = models.PositiveIntegerField(null=True, blank=True)  # Total exam marks
    conversion_total = models.PositiveIntegerField(null=True, blank=True)  # Marks to convert CA (e.g., 40)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"Structure for {self.branch.branch_name} ({self.ca_total} + {self.exam_total})"


class ResultComponent(models.Model):
    structure = models.ForeignKey(
        ResultStructure, 
        on_delete=models.CASCADE, 
        related_name='components', 
        null=True, 
        blank=True
    )
    name = models.CharField(max_length=100, null=True, blank=True)  # Name of the component (e.g., "1st Test")
    max_marks = models.PositiveSmallIntegerField(null=True, blank=True)  # Maximum marks for this component
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )  # Optional subject-specific component
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        subject_info = f" for {self.subject.name}" if self.subject else ""
        return f"{self.name} ({self.max_marks} marks){subject_info}"



class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    component = models.ForeignKey(ResultComponent, on_delete=models.CASCADE, related_name='student_results')
    score = models.PositiveIntegerField(null=True, blank=True)  # Score for this component
    converted_ca = models.PositiveIntegerField(null=True, blank=True)  # Converted CA
    exam_score = models.PositiveIntegerField(null=True, blank=True)  # Exam score
    total_score = models.PositiveIntegerField(null=True, blank=True)  # Total score (CA + Exam)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.component.name} ({self.score})"



class StudentFinalResult(models.Model):
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name="final_results"
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        related_name="final_results"
    )
    session = models.ForeignKey(
        Session, 
        on_delete=models.CASCADE, 
        related_name="final_results"
    )
    term = models.ForeignKey(
        Term, 
        on_delete=models.CASCADE, 
        related_name="final_results"
    )
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        related_name="final_results"
    )
    converted_ca = models.PositiveIntegerField(null=True, blank=True)  # Permanent converted CA
    exam_score = models.PositiveIntegerField(null=True, blank=True)  # Permanent exam score
    total_score = models.PositiveIntegerField(null=True, blank=True)  # Sum of CA and exam
    grade = models.CharField(max_length=5, null=True, blank=True)  # Grade (e.g., A, B, C)
    remarks = models.TextField(null=True, blank=True)  # Teacher's remarks
    highest_score = models.PositiveIntegerField(null=True, blank=True)  # Highest score in the subject
    lowest_score = models.PositiveIntegerField(null=True, blank=True)  # Lowest score in the subject
    average_score = models.FloatField(null=True, blank=True)  # Average score in the subject
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.session.session_name} - {self.term.term_name})"

