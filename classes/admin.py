from django.contrib import admin
from .models import Department, Class, Arm, Subject, SubjectType
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
    list_display = ('name', 'level', 'department', 'display_branches')
    list_filter = ('level', 'department')
    filter_horizontal = ('arms',)
    search_fields = ('name', 'branches__branch_name')

    def display_branches(self, obj):
        return ", ".join(branch.branch_name for branch in obj.branches.all())
    display_branches.short_description = 'Branches'

@admin.register(SubjectType)
class SubjectTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject_code', 'subject_type', 'is_general')
    list_filter = ('subject_type', 'is_general')
    search_fields = ('name', 'subject_code')
    filter_horizontal = ('classes', 'departments')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'subject_type' in request.GET:
            try:
                subject_type_id = int(request.GET.get('subject_type'))
                subject_type = SubjectType.objects.get(pk=subject_type_id)
                if subject_type.level in ['general_primary', 'general_secondary']:
                    form.base_fields['classes'].queryset = Class.objects.all()
                else:
                    form.base_fields['classes'].queryset = Class.objects.filter(level=subject_type.level)
            except (ValueError, TypeError, SubjectType.DoesNotExist):
                form.base_fields['classes'].queryset = Class.objects.none()
        elif obj and obj.subject_type:
            if obj.subject_type.level in ['general_primary', 'general_secondary']:
                form.base_fields['classes'].queryset = Class.objects.all()
            else:
                form.base_fields['classes'].queryset = Class.objects.filter(level=obj.subject_type.level)
        else:
            form.base_fields['classes'].queryset = Class.objects.all()
        return form
