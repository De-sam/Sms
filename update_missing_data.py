import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolproject.settings")
django.setup()

from students.models import Student
from results.models import StudentFinalResult
from classes.models import Class


def fill_missing_classes_and_remarks():
    # Fetch records with missing classes
    missing_classes = StudentFinalResult.objects.filter(student_class__isnull=True)
    missing_remarks = StudentFinalResult.objects.filter(remarks__isnull=True)

    updated_classes_count = 0
    updated_remarks_count = 0

    # Update missing classes
    for result in missing_classes:
        # Detect class from the student object
        student_class = result.student.student_class
        if student_class:
            result.student_class = student_class
            result.save(update_fields=['student_class'])
            updated_classes_count += 1

    print(f"Updated {updated_classes_count} records with missing classes.")

    # Update missing remarks
    for result in missing_remarks:
        # Generate remark based on the grade
        grade = result.grade
        remark = generate_remark(grade) if grade else "No Remark Available"
        result.remarks = remark
        result.save(update_fields=['remarks'])
        updated_remarks_count += 1

    print(f"Updated {updated_remarks_count} records with missing remarks.")


def generate_remark(grade):
    """
    Generate a remark based on the grade.
    """
    remarks = {
        "A1": "Excellent",
        "B2": "Very Good",
        "B3": "Good",
        "C4": "Credit",
        "C5": "Credit",
        "C6": "Credit",
        "D7": "Pass",
        "E8": "Pass",
        "F9": "Fail",
    }
    return remarks.get(grade, "No Remark Available")


if __name__ == "__main__":
    fill_missing_classes_and_remarks()
