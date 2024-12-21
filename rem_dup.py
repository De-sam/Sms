import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolproject.settings")  # Replace with your project name
django.setup()

from comments.models import Comment
from django.db.models import Count

def clean_duplicate_comments():
    """
    Identify and delete duplicate comments while retaining the most recent one.
    A comment is considered duplicate if it shares the same student, session, and term.
    """
    print("Searching for duplicate comments...")

    # Find duplicates based on student, session, and term
    duplicates = (
        Comment.objects.values('student', 'session', 'term')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )

    if not duplicates:
        print("No duplicate comments found.")
        return

    total_deleted = 0

    for duplicate in duplicates:
        student = duplicate['student']
        session = duplicate['session']
        term = duplicate['term']

        # Fetch all duplicates for this combination
        comments = Comment.objects.filter(student=student, session=session, term=term)

        # Keep the most recent comment and delete the rest
        latest_comment = comments.latest('created_at')
        to_delete = comments.exclude(id=latest_comment.id)
        deleted_count = to_delete.delete()[0]

        total_deleted += deleted_count
        print(f"Deleted {deleted_count} duplicates for Student ID {student}, "
              f"Session ID {session}, Term ID {term}. Kept Comment ID {latest_comment.id}.")

    print(f"Total duplicate comments deleted: {total_deleted}")

if __name__ == "__main__":
    clean_duplicate_comments()
