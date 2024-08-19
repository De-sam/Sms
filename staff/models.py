from django.db import models
from django.contrib.auth.models import User
from schools.models import Branch

# Create your models here.
class Role(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Staff(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]

    NATIONALITY_CHOICES = [
        ('nigerian', 'Nigerian'),
        ('non_nigerian', 'Non-Nigerian'),
    ]

    STAFF_CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('non_academic', 'Non-Academic'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    branches = models.ManyToManyField(Branch, related_name='staff')  # Changed to ManyToManyField
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    nationality = models.CharField(max_length=20, choices=NATIONALITY_CHOICES)
    staff_category = models.CharField(max_length=15, choices=STAFF_CATEGORY_CHOICES)
    school_details = models.TextField(blank=True, null=True)  # Additional school-related information
    cv = models.FileField(upload_to='cvs/', blank=True, null=True)  # Field to upload CV
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    staff_signature = models.FileField(upload_to='signatures/', blank=True, null=True)  # Signature upload

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.role.name}"

