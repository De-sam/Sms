from django.db import models

class  SchoolRegistration(models.Model):
    SCHOOL_THEMES = [
        ('theme1', 'Theme 1'),
        ('theme2', 'Theme 2'),
        # Add more themes as needed
    ]
    
    school_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    lga = models.CharField(max_length=100)
    short_code = models.CharField(max_length=50, unique=True)
    logo = models.ImageField(upload_to='logos/')
    theme = models.CharField(max_length=100, choices=SCHOOL_THEMES)
    admin_first_name = models.CharField(max_length=100)
    admin_last_name = models.CharField(max_length=100)
    admin_email = models.EmailField(unique=True)
    admin_phone_number = models.CharField(max_length=15)
    referral_source = models.CharField(max_length=255)
    school_id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"{self.school_name} - Admin: {self.admin_first_name} {self.admin_last_name}, Phone: {self.admin_phone_number}"