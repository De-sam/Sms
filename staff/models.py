from django.db import models
from django.contrib.auth.models import User
from schools.models import Branch

class Role(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        indexes = [
            models.Index(fields=['name']),  # Index on the name for faster lookups
        ]

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

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    branches = models.ManyToManyField(Branch, related_name='staff')
    gender   = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    nationality = models.CharField(max_length=20, choices=NATIONALITY_CHOICES)
    staff_category = models.CharField(max_length=15, choices=STAFF_CATEGORY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    school_details = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='cvs/', blank=False, null=False)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    staff_signature = models.FileField(upload_to='signatures/', blank=False, null=False)

    # New fields for account information
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=10, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)

    # New salary field
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Enter the staff's salary")


    class Meta:
        indexes = [
            models.Index(fields=['user']),  # Index on the user (foreign key)
            models.Index(fields=['role']),  # Index on role (foreign key)
            models.Index(fields=['gender']),  # Index on gender for filtering
            models.Index(fields=['marital_status']),  # Index on marital status for filtering
            models.Index(fields=['status']),  # Index on status (active/inactive) for filtering
            models.Index(fields=['phone_number']),  # Index on phone number for faster lookups
        ]

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.role.name}"
