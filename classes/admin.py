# admin.py
from django.contrib import admin
from .models import Department, Class, Arm
from schools.models import Branch

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Arm)
class ArmAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'display_branches')
    filter_horizontal = ('arms',)
    search_fields = ('name', 'branches__branch_name')  # Update here

    def display_branches(self, obj):
        return ", ".join(branch.branch_name for branch in obj.branches.all())
    
    display_branches.short_description = 'Branches'
