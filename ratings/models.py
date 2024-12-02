from django.db import models
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
    coordination = models.PositiveSmallIntegerField(null=True, blank=True)  # e.g., scale 1-5
    handwriting = models.PositiveSmallIntegerField(null=True, blank=True)
    sports = models.PositiveSmallIntegerField(null=True, blank=True)
    music = models.PositiveSmallIntegerField(null=True, blank=True)

    

    def __str__(self):
        return f"{self.student.full_name()} - {self.session.session_name} - {self.term.term_name}"

class BehavioralRating(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='behavioral_ratings', null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    rating_date = models.DateField(auto_now_add=True)

    # Behavioral traits
    punctuality = models.PositiveSmallIntegerField(null=True, blank=True)  # e.g., scale 1-5
    attentiveness = models.PositiveSmallIntegerField(null=True, blank=True)
    obedience = models.PositiveSmallIntegerField(null=True, blank=True)
    leadership = models.PositiveSmallIntegerField(null=True, blank=True)

    

    def __str__(self):
        return f"{self.student.full_name()} - {self.session.session_name} - {self.term.term_name}"

