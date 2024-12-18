import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolproject.settings")
django.setup()

from results.models import StudentFinalResult, StudentAverageResult
from django.db.models import Sum

def recalculate_student_averages():
    """
    Recalculate total obtainable, total obtained, and average percentage for each student.
    Only include subjects with valid scores.
    """
    # Fetch all StudentAverageResult entries
    student_averages = StudentAverageResult.objects.all()

    total_updated_records = 0

    for student_average in student_averages:
        # Fetch the student's results with valid scores
        student_results = StudentFinalResult.objects.filter(
            student=student_average.student,
            session=student_average.session,
            term=student_average.term,
            branch=student_average.branch,
            converted_ca__gt=0,  # Ensure test scores are valid
            exam_score__gt=0  # Ensure exam scores are valid
        )

        if not student_results.exists():
            # Skip if no valid scores exist
            continue

        # Recalculate total scores
        total_score_obtained = student_results.aggregate(Sum("total_score"))["total_score__sum"] or 0
        total_subjects = student_results.count()
        total_score_maximum = total_subjects * 100  # Assuming max score per subject is 100

        # Update the StudentAverageResult entry
        student_average.total_score_obtained = total_score_obtained
        student_average.total_score_maximum = total_score_maximum

        if total_score_maximum > 0:
            student_average.average_percentage = (total_score_obtained / total_score_maximum) * 100
        else:
            student_average.average_percentage = 0

        # Save the updated average
        student_average.save()
        total_updated_records += 1

        print(f"Student ID {student_average.student.id}: Total Obtained={total_score_obtained}, "
              f"Total Maximum={total_score_maximum}, Average Percentage={student_average.average_percentage:.2f}%")

    print(f"Recalculated averages for a total of {total_updated_records} records.")

if __name__ == "__main__":
    recalculate_student_averages()
