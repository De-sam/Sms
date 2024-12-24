from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_student_creation_email(email, username, short_code, first_name, last_name):
    login_url = f'http://sms-lme5.onrender.com/schools/{short_code}/login/'
    full_name = f"{first_name} {last_name}"
    
    # Email subject and message
    subject = 'Your New Account'
    message = (
        f'Dear {full_name},\n\n'
        f'Your account has been created.\n\n'
        f'Username: "{username}"\n'
        f'Password: "student"\n\n'
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
def send_parent_creation_email(email, username, short_code, first_name, last_name):
    login_url = f'http://sms-lme5.onrender.com/schools/{short_code}/login/'
    full_name = f"{last_name} {first_name} "

    # Email subject and message
    subject = 'Your Parent Account Details'
    message = (
        f'Dear {full_name},\n\n'
        f'Your account has been successfully created.\n\n'
        f'Username: "{username}"\n'
        f'Password: "parent"\n\n'
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