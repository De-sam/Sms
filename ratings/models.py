from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Student
from academics.models import Session, Term
from schools.models import Branch

class PsychomotorRating(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='psychomotor_ratings', null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    rating_date = models.DateField(auto_now_add=True)

    # Psychomotor skills
    coordination = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )  # e.g., scale 1-5
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

    def __str__(self):
        return f"{self.student.full_name()} - {self.session.session_name} - {self.term.term_name}"


class BehavioralRating(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='behavioral_ratings', null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    rating_date = models.DateField(auto_now_add=True)

    # Behavioral traits
    punctuality = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )  # e.g., scale 1-5
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

    def __str__(self):
        return f"{self.student.full_name()} - {self.session.session_name} - {self.term.term_name}"
