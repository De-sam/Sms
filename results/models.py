from django.db import models
from classes.models import Class, Subject
from schools.models import Branch
from students.models import Student  # Assuming you have a Student model
from academics.models import Session, Term
from classes.models import Class, Subject
import uuid



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

    class Meta:
        unique_together = ("branch",)  # Each branch can have only one structure
        indexes = [
            models.Index(fields=["branch"]),  # Speeds up queries by branch
        ]


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

    class Meta:
        unique_together = ("structure", "name", "subject")  # Each component must be unique within a structure
        indexes = [
            models.Index(fields=["structure", "subject"]),  # Speeds up filtering by structure and subject
        ]


    def __str__(self):
        subject_info = f" for {self.subject.name}" if self.subject else ""
        return f"{self.name} ({self.max_marks} marks){subject_info}"



class StudentResult(models.Model):
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='results'
    )
    component = models.ForeignKey(
        ResultComponent, 
        on_delete=models.CASCADE, 
        related_name='student_results'
    )
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="student_results"
    )
    session = models.ForeignKey(
        Session, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True, 
        related_name="student_results"
    )
    term = models.ForeignKey(
        Term, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name="student_results"
    )

    score = models.PositiveIntegerField(null=True, blank=True)  # Score for this componentr this component
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    class Meta:
        unique_together = ("student", "component", "subject")
        indexes = [
            models.Index(fields=["student", "component", "session", "term"]),  # Speeds up student-component lookups
        ]

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
    student_class = models.ForeignKey(  
        Class,
        on_delete=models.CASCADE,
        related_name="final_results",
        null=True, 
        blank=True
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

    class Meta:
        unique_together = ('student', 'session', 'term', 'branch', 'student_class', 'subject')
        indexes = [
            models.Index(fields=["student", "session", "term", "subject"]),  # Optimizes result queries by session, term, and subject
        ]
        verbose_name = "Student Final Result"
        verbose_name_plural = "Student Final Results"

    def save(self, *args, **kwargs):
        # Check for existing records with the same unique constraints
        if not self.pk:  # Only check for existing records if this is a new instance
            existing_record = StudentFinalResult.objects.filter(
                student=self.student,
                session=self.session,
                term=self.term,
                branch=self.branch,
                student_class=self.student_class,
                subject=self.subject
            ).first()

            if existing_record:
                # Update the existing record fields
                existing_record.converted_ca = self.converted_ca
                existing_record.exam_score = self.exam_score
                existing_record.total_score = self.total_score
                existing_record.grade = self.grade
                existing_record.remarks = self.remarks
                existing_record.highest_score = self.highest_score
                existing_record.lowest_score = self.lowest_score
                existing_record.average_score = self.average_score
                existing_record.save(update_fields=[
                    "converted_ca", "exam_score", "total_score", "grade", "remarks",
                    "highest_score", "lowest_score", "average_score"
                ])
                return  # Exit to prevent saving the duplicate record

        # Proceed with the default save behavior for new or updated records
        super().save(*args, **kwargs)


class StudentAverageResult(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="average_results"
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="average_results"
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="average_results"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="average_results"
    )
    total_score_obtained = models.PositiveIntegerField(default=0)  # Sum of scores the student obtained
    total_score_maximum = models.PositiveIntegerField(default=0)  # Total possible score
    average_percentage = models.FloatField(null=True, blank=True)  # Calculated percentage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "session", "term", "branch")
        indexes = [
            models.Index(fields=["student", "session", "term"]),  # Optimize average result queries
        ]

    def __str__(self):
        return f"{self.student} - {self.session.session_name} ({self.term.term_name})"

    def calculate_average(self):
        """
        Calculate the average percentage and update the field,
        excluding subjects with invalid scores.
        """
        from results.models import StudentFinalResult  # Import here to avoid circular dependencies

        # Fetch results with valid scores
        student_results = StudentFinalResult.objects.filter(
            student=self.student,
            session=self.session,
            term=self.term,
            branch=self.branch,
            converted_ca__gt=0,  # Ensure test scores are valid
            exam_score__gt=0  # Ensure exam scores are valid
        )

        # Aggregate total scores
        total_score_obtained = student_results.aggregate(Sum("total_score"))["total_score__sum"] or 0

        # Count valid subjects
        total_subjects = student_results.count()
        total_score_maximum = total_subjects * 100  # Assuming max score per subject is 100

        # Update instance fields
        self.total_score_obtained = total_score_obtained
        self.total_score_maximum = total_score_maximum

        # Calculate average percentage
        if total_score_maximum > 0:
            self.average_percentage = (total_score_obtained / total_score_maximum) * 100
        else:
            self.average_percentage = 0

        self.save()

    def __str__(self):
        return f"{self.student} - {self.session.session_name} ({self.term.term_name})"


class PublishedResult(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    cls = models.ForeignKey(Class, on_delete=models.CASCADE)  # The class for which results are published
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('session', 'term', 'branch', 'cls')  # Ensure no duplicate entries for the same class
        indexes = [
            models.Index(fields=["session", "term", "branch", "cls"]),  # Optimize result publication queries
        ]

    def __str__(self):
        return f"{self.cls} - {self.session} {self.term} (Published: {self.is_published})"


class GradingSystem(models.Model):
    """
    Represents a grading system for a branch.
    """
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="grading_systems",
        null=True,
        blank=True,
        db_index=True  # Index for optimized queries
    )
    grade = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        db_index=True  # Index for optimized queries
    )  # e.g., A1, B2
    lower_bound = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True  # Index for optimized queries
    )  # Minimum percentage for the grade
    upper_bound = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True  # Index for optimized queries
    )  # Maximum percentage for the grade
    remark = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )  # Remark associated with the grade

    class Meta:
        unique_together = ("branch", "grade")  # Ensure grades are unique per branch
        ordering = ['-lower_bound']  # Order by descending lower bound for grading logic
        indexes = [  # Additional indexing for optimized queries
            models.Index(fields=['branch', 'grade']),
            models.Index(fields=['lower_bound']),
            models.Index(fields=['upper_bound']),
        ]

    def __str__(self):
        return f"{self.grade} ({self.lower_bound}% - {self.upper_bound}%) - {self.remark}"

class ResultVerificationToken(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="verification_tokens")
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'session', 'term', 'branch')

    def __str__(self):
        return f"Token for {self.student} ({self.session}, {self.term})"
    
    def get_verification_url(self, request=None):
        from django.urls import reverse
        path = reverse("verify_result", kwargs={
            "short_code": self.branch.school.short_code,
            "token": str(self.token)
        })

        if request:
            return request.build_absolute_uri(path)
        return path