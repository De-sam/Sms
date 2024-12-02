from django.contrib import admin
from .models import SchoolDaysOpen, StudentAttendance
from academics.models import Session, Term
from schools.models import Branch
from classes.models import Class
from students.models import Student

# Customize the SchoolDaysOpen admin
@admin.register(SchoolDaysOpen)
class SchoolDaysOpenAdmin(admin.ModelAdmin):
    list_display = ('branch', 'session', 'term', 'days_open', 'created_at', 'updated_at')
    search_fields = ('branch__branch_name', 'session__session_name', 'term__term_name')
    list_filter = ('branch', 'session', 'term')
    ordering = ('branch', 'session', 'term')
    list_editable = ('days_open',)  # Allow inline editing of the "days_open" field

# Customize the StudentAttendance admin
@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'student_class', 'session', 'term', 'branch', 'attendance_count', 'date', 'created_at')
    search_fields = (
        'student__first_name', 
        'student__last_name', 
        'student_class__name', 
        'branch__branch_name', 
        'session__session_name', 
        'term__term_name'
    )
    list_filter = ('student_class', 'session', 'term', 'branch')
    ordering = ('student_class', 'student', 'session', 'term', 'date')
    date_hierarchy = 'date'  # Adds a date hierarchy for filtering by date

    def get_queryset(self, request):
        # Optimized queryset to reduce database hits
        return super().get_queryset(request).select_related(
            'student', 'student_class', 'session', 'term', 'branch'
        )
