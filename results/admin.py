from django.contrib import admin
from .models import ResultStructure, ResultComponent, StudentResult,StudentFinalResult,StudentAverageResult

class ResultComponentInline(admin.TabularInline):
    model = ResultComponent
    extra = 1
    fields = ('name', 'max_marks', 'subject')
    ordering = ('created_at',)  # Ensures components are ordered by creation time

@admin.register(ResultStructure)
class ResultStructureAdmin(admin.ModelAdmin):
    list_display = ('branch', 'ca_total', 'exam_total', 'conversion_total', 'created_at')
    search_fields = ('branch__branch_name',)
    list_filter = ('branch',)
    inlines = [ResultComponentInline]

@admin.register(ResultComponent)
class ResultComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'structure', 'max_marks', 'subject', 'created_at')
    search_fields = ('name', 'structure__branch__branch_name', 'subject__name')
    list_filter = ('structure', 'subject')

@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'component', 'score', 'converted_ca', 'exam_score', 'total_score', 'created_at')
    search_fields = ('student__first_name', 'student__last_name', 'component__name')
    list_filter = ('component__structure', 'component', 'student')
    ordering = ('-created_at',)  # Order by most recent first
    actions = ['remove_duplicates']

    def remove_duplicates(self, request, queryset):
        """
        Custom admin action to remove duplicate StudentResult entries.
        """
        from collections import defaultdict
        duplicates = defaultdict(list)

        for result in queryset:
            duplicates[(result.student_id, result.component_id)].append(result)

        removed_count = 0
        for (student_id, component_id), results in duplicates.items():
            if len(results) > 1:
                # Keep the first result and delete others
                results_to_delete = results[1:]
                removed_count += len(results_to_delete)
                for result in results_to_delete:
                    result.delete()

        self.message_user(request, f"Removed {removed_count} duplicate StudentResult entries.")

    remove_duplicates.short_description = "Remove duplicate StudentResult entries"


@admin.register(StudentFinalResult)
class StudentFinalResultAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'branch',
        'session',
        'term',
        'subject',
        'converted_ca',
        'exam_score',
        'total_score',
        'grade',
        'highest_score',  # New field
        'lowest_score',   # New field
        'average_score',  # New field
        'created_at'
    )
    search_fields = (
        'student__first_name',
        'student__last_name',
        'branch__branch_name',
        'subject__name',
        'session__session_name',
        'term__term_name'
    )
    list_filter = (
        'branch',
        'session',
        'term',
        'subject',
        'grade'  # Added filter by grade
    )
    ordering = ('-created_at',)  # Order by most recent first
    readonly_fields = ('highest_score', 'lowest_score', 'average_score')  # Make new fields read-only

    def get_queryset(self, request):
        """
        Optimize the queryset by prefetching related fields.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('student', 'branch', 'session', 'term', 'subject')

    def has_change_permission(self, request, obj=None):
        """
        Allow change permissions but restrict modifications to read-only fields.
        """
        if obj:
            readonly_fields = self.readonly_fields
            self.readonly_fields = ('highest_score', 'lowest_score', 'average_score')
        return super().has_change_permission(request, obj)

@admin.register(StudentAverageResult)
class StudentAverageResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "session",
        "term",
        "branch",
        "total_score_obtained",
        "total_score_maximum",
        "average_percentage",
        "created_at",
    )
    search_fields = ("student__first_name", "student__last_name", "session__session_name", "term__term_name")
    list_filter = ("session", "term", "branch")
    ordering = ("-created_at",)


