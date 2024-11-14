# students/models.py
from django.db import models
from django.contrib.auth.models import User  # Use the built-in User model for authentication
from classes.models import Class
from schools.models import Branch

class ParentGuardian(models.Model):
    TITLE_CHOICES = [
        ('mr', 'Mr'),
        ('mrs', 'Mrs'),
        ('ms', 'Ms'),
        ('dr', 'Dr'),
        ('prof', 'Prof'),
        ('rev', 'Rev'),
        ('sir', 'Sir'),
        ('lady', 'Lady'),
    ]

    # Linking to the User model for authentication
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="parent_profile"  # Add related_name for reverse access
    )    
    title = models.CharField(max_length=10, choices=TITLE_CHOICES, blank=True, null=True)  # Title field
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)  # Required for login
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        title_display = f"{self.get_title_display()} " if self.title else ""
        return f"{title_display}{self.first_name} {self.last_name} - {self.phone_number}"
    

class ParentStudentRelationship(models.Model):
    RELATION_TYPE_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),   
        ('guardian', 'Guardian'),
        ('grandfather', 'Grandfather'),
        ('grandmother', 'Grandmother'),
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    ]

    parent_guardian = models.ForeignKey(ParentGuardian, on_delete=models.CASCADE, related_name='relationships')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='relationships')
    relation_type = models.CharField(max_length=20, choices=RELATION_TYPE_CHOICES)

    class Meta:
        # This constraint prevents the same parent from being linked to the same student more than once
        unique_together = ('student', 'parent_guardian')
        
    def __str__(self):
        return f"{self.parent_guardian} is {self.get_relation_type_display()} of {self.student}"

class Student(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    NATIONALITY_CHOICES = [
        ('nigerian', 'Nigerian'),
        ('non_nigerian', 'Non-Nigerian'),
    ]

    # User authentication (linked to Django's User model)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')

    # Student personal details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    guardians = models.ManyToManyField(ParentGuardian, through='ParentStudentRelationship', related_name='students')
    date_of_birth = models.DateField()
    student_id = models.CharField(max_length=20, unique=True, editable=False)  # Generated on save
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    peculiar_illnesses = models.TextField(blank=True, null=True)
    nationality = models.CharField(max_length=20, choices=NATIONALITY_CHOICES)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='students/profile_pictures/', blank=True, null=True)

    # Class and academic information
    admission_date = models.DateField()
    last_admitted_class = models.CharField(max_length=100)  # Last class admitted into
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')  
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)  

    # Status tracking
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # Timestamps for record tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.student_id})"

    def save(self, *args, **kwargs):
        # Automatically generate a unique student ID if not provided
        if not self.student_id:
            self.student_id = f"STU{str(self.user.id).zfill(5)}"  # Example: STU00001
        
        super(Student, self).save(*args, **kwargs)

    @property
    def age(self):
        from datetime import date
        return date.today().year - self.date_of_birth.year

    class Meta:
        indexes = [
            models.Index(fields=['first_name', 'last_name']),  # Index for searching students by name
            models.Index(fields=['student_id']),  # Unique index for student ID
            models.Index(fields=['student_class']),  # Foreign key index for class
            models.Index(fields=['user']),  # Index on user for authentication
            models.Index(fields=['status']),  # Index on status (active/inactive)
        ]

class StudentTransferLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transfer_logs')
    old_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='old_transfers')
    new_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='new_transfers')
    transfer_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} transferred from {self.old_branch} to {self.new_branch} on {self.transfer_date}"
