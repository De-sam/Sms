from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Student
from academics.models import Session, Term
from schools.models import Branch
from landingpage.models import SchoolRegistration


class RatingCriteria(models.Model):
    RATING_TYPE_CHOICES = [
        ('psychomotor', 'Psychomotor'),
        ('behavioral', 'Behavioral'),
    ]

    school = models.ForeignKey(
        SchoolRegistration, 
        on_delete=models.CASCADE, 
        related_name='rating_criteria',
        null=True,
        blank=True
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='rating_criteria'
    )
    rating_type = models.CharField(
        max_length=15, 
        choices=RATING_TYPE_CHOICES,
        null=True,
        blank=True
    )
    criteria_name = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    max_value = models.PositiveSmallIntegerField(
        default=5, 
        validators=[MinValueValidator(1)],
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'branch', 'rating_type', 'criteria_name'],
                name='unique_rating_criteria_per_branch'
            )
        ]
        indexes = [
            models.Index(fields=['school', 'branch']),
            models.Index(fields=['rating_type']),
        ]

    def __str__(self):
        return f"{self.criteria_name} ({self.rating_type}) - {self.school.school_name}"


class Rating(models.Model):
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='ratings',
        null=True,
        blank=True
    )
    session = models.ForeignKey(
        Session, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    term = models.ForeignKey(
        Term, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    rating_type = models.CharField(
        max_length=15, 
        choices=RatingCriteria.RATING_TYPE_CHOICES,
        null=True,
        blank=True
    )
    criteria = models.ForeignKey(
        RatingCriteria, 
        on_delete=models.CASCADE, 
        related_name='ratings',
        null=True,
        blank=True
    )
    value = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    rating_date = models.DateField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'session', 'term', 'branch', 'criteria'],
                name='unique_rating_per_student'
            )
        ]
        indexes = [
            models.Index(fields=['student', 'session', 'term']),
            models.Index(fields=['branch', 'rating_type']),
        ]

    def __str__(self):
        criteria_name = self.criteria.criteria_name if self.criteria else "Unspecified Criteria"
        value = self.value if self.value is not None else "None"
        return f"{self.student.full_name()} - {criteria_name}: {value}"
    
    def to_dict(self):
        return {
            "criteria": self.criteria.criteria_name if self.criteria else None,
            "value": self.value,
        }
