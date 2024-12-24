from celery import shared_task
from landingpage.models import SchoolRegistration
import os
import time
from django.conf import settings
from django.core.mail import send_mail



@shared_task
def process_file_task(file_path, file_name, school_id):
    """internal imports"""
    from staff.utils import process_uploaded_file, extract_branch_from_filename

    try:
        school = SchoolRegistration.objects.get(id=school_id)
        branch = extract_branch_from_filename(file_name, school)
        
        if branch:
            with open(file_path, 'rb') as file:
                process_uploaded_file(file, file_name, branch, school)
        else:
            print(f"Branch could not be detected for file {file_name}")
    except Exception as e:
        print(f"Error processing file task: {e}")
        raise  # Re-raise the exception so it can be tracked by Celery


@shared_task
def send_staff_creation_email(email, username, shortcode):
    
    login_url = f'http://sms-lme5.onrender.com/schools/{shortcode}/login/'
    
    # Email subject and message
    subject = 'Your New Account'
    message = (
        f'Your account has been created.\n\n'
        f'Username: "{username}"\n'
        f'Password: "new_staff"\n\n'
        f'Please log in using the following URL: {login_url}\n'
        f'Remember to change your password after your first login.'
    )
    from_email = 'admin@example.com'  # Update this with your admin email
    try:
        send_mail(
            subject,
            message,
            from_email,
            [email],
        )
        print(f"Email sent to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")

@shared_task
def delete_temp_files():
    """
    Task to delete files from the 'temp_files' directory older than 1 minute.
    """
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_files')
    
    if not os.path.exists(temp_dir):
        return  # Directory does not exist, so nothing to delete

    # Get the current time
    now = time.time()

    # Iterate over the files in the temp_files directory
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        
        # Check if the file is older than 60 seconds (1 minute)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > 60:  # File older than 1 minute
                os.remove(file_path)  # Delete the file
                print(f"Deleted old temp file: {file_path}")