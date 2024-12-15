from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Student
from academics.models import Session, Term
from schools.models import Branch


class Rating(models.Model):
    RATING_TYPE_CHOICES = [
        ('psychomotor', 'Psychomotor'),
        ('behavioral', 'Behavioral'),
    ]

    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='ratings'
    )
    session = models.ForeignKey(
        Session, 
        on_delete=models.CASCADE
    )
    term = models.ForeignKey(
        Term, 
        on_delete=models.CASCADE
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE
    )
    rating_type = models.CharField(
        max_length=15, 
        choices=RATING_TYPE_CHOICES, 
        default='psychomotor'
    )
    rating_date = models.DateField(auto_now_add=True)

    # Psychomotor fields
    coordination = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    handwriting = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    sports = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    artistry = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    verbal_fluency = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    games = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
 
    # Behavioral fields
    punctuality = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    attentiveness = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    obedience = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    leadership = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    emotional_stability = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    teamwork = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    neatness = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"{self.student.full_name()} - {self.session.session_name} - {self.term.term_name} ({self.rating_type})"

    def is_psychomotor(self):
        return self.rating_type == 'psychomotor'

    def is_behavioral(self):
        return self.rating_type == 'behavioral'
