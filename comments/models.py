from django.db import models
from students.models import Student
from academics.models import Session, Term
from django.conf import settings

class Comment(models.Model):
    """
    Model to store comments for students based on session and term.
    """
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='comments',
        help_text="The student this comment is for."
    )
    session = models.ForeignKey(
        Session, 
        on_delete=models.CASCADE,
        help_text="The academic session for this comment."
    )
    term = models.ForeignKey(
        Term, 
        on_delete=models.CASCADE,
        help_text="The term for this comment."
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        help_text="The user who wrote this comment."
    )
    comment_text = models.TextField(
        help_text="The content of the comment."
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="The date and time when the comment was created."
    )

    def __str__(self):
        return f"Comment by {self.author} on {self.student} ({self.session} - {self.term})"
