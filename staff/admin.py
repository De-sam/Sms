from django.contrib import admin
from .models import Staff, Role
from classes.models import TeacherSubjectClassAssignment

class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'gender', 'marital_status', 'phone_number', 'nationality', 'staff_category', 'status')
    list_filter = ('role', 'gender', 'marital_status', 'nationality', 'staff_category', 'status')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'phone_number', 'address')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'branches', 'staff_category', 'status')
        }),
        ('Personal Info', {
            'fields': ('gender', 'marital_status', 'date_of_birth', 'phone_number', 'address', 'nationality')
        }),
        ('Professional Details', {
            'fields': ('school_details', 'cv', 'profile_picture', 'staff_signature')
        }),
    )
    filter_horizontal = ('branches',)  # Allows selecting multiple branches with a horizontal filter box

admin.site.register(Staff, StaffAdmin)
admin.site.register(Role)

class TeacherSubjectClassAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'get_classes_assigned')
    filter_horizontal = ('classes_assigned',)
    list_filter = ('teacher', 'subject')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name', 'subject__name')

    def get_classes_assigned(self, obj):
        return ", ".join([cls.name for cls in obj.classes_assigned.all()])
    get_classes_assigned.short_description = 'Classes Assigned'

admin.site.register(TeacherSubjectClassAssignment, TeacherSubjectClassAssignmentAdmin)