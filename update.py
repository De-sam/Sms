import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolproject.settings")
django.setup()

from results.models import StudentFinalResult
from django.db.models import Max, Min, Avg

def recalculate_scores():
    """
    Recalculate highest, lowest, and average scores for each class.
    Exclude zero from the lowest score calculation.
    """
    # Fetch distinct classes from the StudentFinalResult model
    classes = StudentFinalResult.objects.values_list('student_class', flat=True).distinct()

    total_updated_records = 0

    for student_class in classes:
        # Filter results for each class
        results = StudentFinalResult.objects.filter(student_class=student_class)

        if not results.exists():
            continue

        # Calculate the highest, lowest (excluding zeros), and average scores for the class
        highest_score = results.aggregate(Max('total_score'))['total_score__max'] or 0
        lowest_score = results.exclude(total_score=0).aggregate(Min('total_score'))['total_score__min'] or 0
        average_score = results.aggregate(Avg('total_score'))['total_score__avg'] or 0

        # Update all records in this class with the recalculated values
        results.update(
            highest_score=highest_score,
            lowest_score=lowest_score,
            average_score=round(average_score, 2) if average_score else 0
        )

        class_record_count = results.count()
        total_updated_records += class_record_count

        print(f"Class ID {student_class}: Highest={highest_score}, Lowest={lowest_score}, Average={round(average_score, 2) if average_score else 0}, Records Updated={class_record_count}")

    print(f"Recalculated scores for a total of {total_updated_records} records.")

if __name__ == "__main__":
    recalculate_scores()
