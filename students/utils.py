# students/utils.py
import uuid
from datetime import datetime
from landingpage.models import SchoolRegistration
from .models import Student

def generate_student_id(school_name):
    # Extract initials from school name
    initials = ''.join([word[0].upper() for word in school_name.split()])
    
    # Get the current year
    current_year = datetime.now().year
    
    # Count existing students for this school and year
    existing_students = Student.objects.filter(student_id__startswith=f"{initials}/{current_year}").count()
    counter = existing_students + 1  # Increment counter
    
    # Format student ID as SchoolInitials/Year/Counter
    return f"{initials}/{current_year}/{counter:03d}"


def generate_student_username(first_name, last_name, student_id):
    # First letter of the last name and full first name
    username_part = f"{last_name[0].upper()}{first_name}"

    # Append the student ID
    return f"{username_part}_{student_id}"
