from django.db import models
from django.contrib.auth.models import User
from landingpage.models import SchoolRegistration
import uuid

class Branch(models.Model):
    school = models.ForeignKey(
        SchoolRegistration, 
        on_delete=models.CASCADE, 
        related_name='branches', 
        null=True, 
        blank=True
    )
    primary_school = models.ForeignKey(
        'PrimarySchool', 
        on_delete=models.CASCADE, 
        related_name='primary_branches', 
        null=True, 
        blank=True
    )
    branch_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['branch_name']),  # Index on branch name for filtering
            models.Index(fields=['school']),       # Foreign key index for faster joins
            models.Index(fields=['primary_school'])  # Foreign key index for faster joins
        ]

    def __str__(self):
        if self.primary_school:
            return f"{self.primary_school.school_name} - {self.branch_name}(Primary)"
        elif self.school:
            return f"{self.school.school_name} - {self.branch_name} (Secondary)"
        return f"Branch: {self.branch_name}"


class PrimarySchool(models.Model):
    parent_school = models.OneToOneField(
        SchoolRegistration,
        on_delete=models.CASCADE,
        related_name='primary_school',
    )
    secondary_school = models.ForeignKey(
        SchoolRegistration,
        on_delete=models.CASCADE,
        related_name='primary_schools',
        null=True, 
        blank=True
    )
    pry_school_id = models.CharField(max_length=10, unique=True, editable=False)
    school_name = models.CharField(max_length=255)
    logo = models.ImageField(default='default.jpeg', upload_to='logos')
    address = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['school_name']),  # Index for filtering by school name
            models.Index(fields=['pry_school_id']),  # Index on unique school ID
            models.Index(fields=['secondary_school'])  # Foreign key index for joins
        ]

    def save(self, *args, **kwargs):
        if not self.pry_school_id:
            school_prefix = self.school_name[:3].upper() if self.school_name else 'XXX'
            uuid_part = str(uuid.uuid4().hex[:6].upper())
            self.pry_school_id = f"{school_prefix}{uuid_part}"

        super().save(*args, **kwargs)

    def __str__(self):
        return (f"ID: {self.pry_school_id}, School Name: {self.school_name}, Address: {self.address}")
