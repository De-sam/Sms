from django.db import models
from django.contrib.auth.models import User

class School(models.Model):
    short_code = models.CharField(max_length=10, unique=True)
    school_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    lga = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logos/')
    theme = models.CharField(max_length=50)
    admin = models.OneToOneField(User, on_delete=models.CASCADE)
    referral_source = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.school_name} - Admin: {self.admin_first_name}\
              {self.admin_last_name}, Phone: {self.admin_phone_number}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_password_changed = models.BooleanField(default=False)

