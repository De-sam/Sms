from celery import shared_task
from landingpage.models import SchoolRegistration
from schools.models import Branch
from django.core.mail import send_mail



@shared_task
def process_file_task(file_path, file_name, school_id):
    """internal imports"""
    from staff.utils import process_uploaded_file, extract_branch_from_filename

    
    school = SchoolRegistration.objects.get(id=school_id)
    branch = extract_branch_from_filename(file_name, school)
    if branch:
        with open(file_path, 'rb') as file:
            process_uploaded_file(file, file_name, branch, school)


@shared_task
def send_staff_creation_email(email, username, shortcode):
    
    login_url = f'http://localhost:8000/schools/{shortcode}/login/'
    
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