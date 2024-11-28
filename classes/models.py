from django.db import models
import uuid
from schools.models import Branch
from staff.models import Staff
from academics.models import Session,Term

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

    class Meta:
        indexes = [
            models.Index(fields=['name']),  # Index for quick lookups by name
            models.Index(fields=['level'])  # Index for level to optimize filtering
        ]

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        indexes = [models.Index(fields=['name'])]  # Index for quick lookup by name

    def __str__(self):
        return self.name


class Arm(models.Model):
    name = models.CharField(max_length=10, unique=True)

    class Meta:
        indexes = [models.Index(fields=['name'])]  # Index for quick lookup by name

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

    class Meta:
        indexes = [
            models.Index(fields=['name']),    # Index on class name for searching
            models.Index(fields=['level']),   # Index on level for filtering
            models.Index(fields=['department'])  # Foreign key indexing for joins with department
        ]

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

    class Meta:
        indexes = [
            models.Index(fields=['name']),           # Index on subject name for searching
            models.Index(fields=['subject_code']),   # Index on unique subject code for quick lookups
            models.Index(fields=['subject_type']),   # Foreign key indexing for subject type
        ]

    def save(self, *args, **kwargs):
        if not self.subject_code:
            prefix = (self.subject_code_prefix or self.name[:3]).upper()
            unique_id = str(uuid.uuid4())[:3].upper()
            existing_codes = Subject.objects.filter(subject_code__startswith=prefix).count() + 1
            sequence = f"{existing_codes:02d}"
            self.subject_code = f"{prefix}-{unique_id}-{sequence}"

        super().save(*args, **kwargs)

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
    session = models.ForeignKey('academics.Session', on_delete=models.CASCADE, related_name='teacher_assignments')  # Use qualified reference
    term = models.ForeignKey('academics.Term', on_delete=models.CASCADE, related_name='teacher_assignments')  # Use qualified reference

    class Meta:
        unique_together = ('teacher', 'subject', 'branch', 'session', 'term')
        indexes = [
            models.Index(fields=['teacher']),  # Index to speed up queries involving teacher
            models.Index(fields=['subject']),  # Index to optimize subject-based filtering
            models.Index(fields=['branch']),   # Index to optimize branch-based filtering
            models.Index(fields=['session']),  # Index to optimize session-based filtering
            models.Index(fields=['term']),     # Index to optimize term-based filtering
        ]

    def __str__(self):
        return f"{self.teacher.user.first_name} {self.teacher.user.last_name} teaches {self.subject.name} in {self.session.session_name}, {self.term.term_name}"