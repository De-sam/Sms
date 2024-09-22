from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_student_creation_email(email, username, short_code):
    
    login_url = f'http://localhost:8000/schools/{short_code}/login/'
    
    # Email subject and message
    subject = 'Your New Account'
    message = (
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

