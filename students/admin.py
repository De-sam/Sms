# admin.py
from django.contrib import admin
from .models import Student, ParentGuardian, ParentStudentRelationship, StudentTransferLog

class ParentStudentRelationshipInline(admin.TabularInline):
    model = ParentStudentRelationship
    extra = 1  # Number of extra empty forms to display

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name')
    search_fields = ('first_name', 'last_name')
    inlines = [ParentStudentRelationshipInline]

@admin.register(ParentGuardian)
class ParentGuardianAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'email')
    search_fields = ('first_name', 'last_name', 'phone_number')
    inlines = [ParentStudentRelationshipInline]

@admin.register(ParentStudentRelationship)
class ParentStudentRelationshipAdmin(admin.ModelAdmin):
    list_display = ('parent_guardian', 'student', 'relation_type')
    search_fields = ('parent_guardian__first_name', 'parent_guardian__last_name', 'student__first_name', 'student__last_name')
    list_filter = ('relation_type',)

@admin.register(StudentTransferLog)
class StudentTransferLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'old_branch', 'new_branch', 'transfer_date')
    search_fields = ('student__first_name', 'student__last_name')
    list_filter = ('transfer_date',)
