from django.db import models
import uuid
from schools.models import Branch
from staff.models import Staff

class SubjectType(models.Model):
    LEVEL_CHOICES = [
        ('creche', 'Creche'),
        ('kindergarten', 'Kindergarten'),
        ('nursery', 'Nursery'),
        ('lower_primary', 'Lower Primary'),
        ('upper_primary', 'Upper Primary'),
        ('junior_secondary', 'Junior Secondary'),
        ('senior_secondary', 'Senior Secondary'),
        ('general_primary', 'General Primary'),
        ('general_secondary', 'General Secondary'),
    ]

    name = models.CharField(max_length=50, unique=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Arm(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Class(models.Model):
    LEVEL_CHOICES = [
        ('creche', 'Creche'),
        ('kindergarten', 'Kindergarten'),
        ('nursery', 'Nursery'),
        ('upper_primary', 'Upper Primary'),
        ('lower_primary', 'Lower Primary'),
        ('junior_secondary', 'Junior Secondary'),
        ('senior_secondary', 'Senior Secondary'),
    ]

    name = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    arms = models.ManyToManyField(Arm, blank=True)
    branches = models.ManyToManyField(Branch, related_name='classes', blank=True)
    class_teachers = models.ManyToManyField(Staff, related_name='class_teacher_of', blank=True) 

    def __str__(self):
        return f"{self.name} ({self.get_level_display()}) {self.department.name if self.department else ''}"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    subject_code_prefix = models.CharField(max_length=3, blank=True, null=True)
    subject_code = models.CharField(max_length=50, unique=True, editable=False)
    description = models.TextField(null=True, blank=True)
    subject_type = models.ForeignKey(SubjectType, on_delete=models.CASCADE)
    departments = models.ManyToManyField(Department, blank=True)
    is_general = models.BooleanField(default=False)
    classes = models.ManyToManyField(Class, related_name='subjects', blank=True)

    def save(self, *args, **kwargs):
        if not self.subject_code:
            prefix = (self.subject_code_prefix or self.name[:3]).upper()
            unique_id = str(uuid.uuid4())[:3].upper()
            existing_codes = Subject.objects.filter(subject_code__startswith=prefix).count() + 1
            sequence = f"{existing_codes:02d}"
            self.subject_code = f"{prefix}-{unique_id}-{sequence}"

        super().save(*args, **kwargs)

        # Automatically link General subjects to appropriate classes
        if self.is_general:
            if self.subject_type.level == 'general_primary':
                self.classes.set(Class.objects.filter(level='primary'))
            elif self.subject_type.level == 'general_secondary':
                self.classes.set(Class.objects.filter(level__in=['junior_secondary', 'senior_secondary']))

    def __str__(self):
        return f"{self.name} ({self.subject_code})"

class TeacherSubjectClassAssignment(models.Model):
    teacher = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='subject_class_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teacher_assignments')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='subject_assignments')
    classes_assigned = models.ManyToManyField(Class, related_name='teacher_subject_classes')

    class Meta:
        unique_together = ('teacher', 'subject','branch')

    def __str__(self):
        return f"{self.teacher.user.first_name} {self.teacher.user.last_name} teaches {self.subject.name}"