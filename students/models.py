# students/models.py
from django.db import models
from django.contrib.auth.models import User  # Use the built-in User model for authentication
from classes.models import Class
from schools.models import Branch
from landingpage.models import SchoolRegistration
from academics.models import Session 

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

    parent_id = models.CharField(max_length=10, unique=True, editable=False)
    school = models.ForeignKey(
        SchoolRegistration, 
        on_delete=models.CASCADE, 
        related_name='parents'
    )  # Directly link parents to schools
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="parent_profile"
    )
    title = models.CharField(max_length=10, choices=TITLE_CHOICES, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        title_display = f"{self.get_title_display()} " if self.title else ""
        return f"{self.last_name} {self.first_name} ({title_display}) - {self.phone_number}"

    def save(self, *args, **kwargs):
        if not self.parent_id:
            latest_parent = ParentGuardian.objects.order_by('-id').first()
            if latest_parent and latest_parent.parent_id:
                latest_id = int(latest_parent.parent_id[1:])
                new_id = f"P{str(latest_id + 1).zfill(3)}"
            else:
                new_id = "P001"
            self.parent_id = new_id
        super().save(*args, **kwargs)


    

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

    current_session = models.ForeignKey(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrolled_students'
    )

    # Student personal details (existing fields unchanged)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    guardians = models.ManyToManyField(ParentGuardian, through='ParentStudentRelationship', related_name='students')
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    date_of_birth = models.DateField()
    student_id = models.CharField(max_length=20, unique=True, editable=False)
    blood_group = models.CharField(max_length=3, choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], blank=True, null=True)
    peculiar_illnesses = models.TextField(blank=True, null=True)
    nationality = models.CharField(max_length=20, choices=[
        ('nigerian', 'Nigerian'), ('non_nigerian', 'Non-Nigerian')
    ])
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='students/profile_pictures/', blank=True, null=True)
    
    admission_date = models.DateField()
    last_admitted_class = models.CharField(max_length=100)  # Last class admitted into
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=10, choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_name(self):
        return f"{self.last_name} {self.first_name}"

    def __str__(self):
        return f"{self.last_name}  {self.first_name} (ID: {self.student_id}) - {self.current_session.session_name if self.current_session else 'No Session'}"

    def save(self, *args, **kwargs):
        # Automatically generate a unique student ID if not provided
        if not self.student_id:
            self.student_id = f"STU{str(self.user.id).zfill(5)}"  # Example: STU00001

        # Set current session if it's not set and there is an active session for the school
        if not self.current_session:
            active_session = Session.objects.filter(is_active=True, school=self.branch.school).first()
            if active_session:
                self.current_session = active_session

        super(Student, self).save(*args, **kwargs)

    @property
    def age(self):
        from datetime import date
        return date.today().year - self.date_of_birth.year

    class Meta:
        indexes = [
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['student_id']),
            models.Index(fields=['student_class']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['current_session']),  # Added index for session
        ]


class StudentTransferLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transfer_logs')
    old_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='old_transfers')
    new_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='new_transfers')
    transfer_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} transferred from {self.old_branch} to {self.new_branch} on {self.transfer_date}"
