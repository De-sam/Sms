from django.contrib import admin
from .models import ResultStructure, ResultComponent, StudentResult, StudentComponentScore

@admin.register(ResultStructure)
class ResultStructureAdmin(admin.ModelAdmin):
    list_display = ('session', 'term', 'branch', 'ca_total', 'exam_total', 'conversion_total', 'created_at')
    list_filter = ('session', 'term', 'branch')  # Remove 'subject' from here
    ordering = ('session', 'term', 'branch')  # Remove 'subject' from here
    search_fields = ('session__session_name', 'term__term_name', 'branch__branch_name')
    # Inline for managing components directly within the structure
    class ResultComponentInline(admin.TabularInline):
        model = ResultComponent
        extra = 1  # Number of empty forms displayed
        fields = ('name', 'max_marks', 'order')
        ordering = ('order',)

    inlines = [ResultComponentInline]

@admin.register(ResultComponent)
class ResultComponentAdmin(admin.ModelAdmin):
    list_display = ('structure', 'name', 'max_marks', 'order')
    list_filter = ('structure__branch', 'structure__session', 'structure__term')
    search_fields = ('structure__branch__name', 'name')
    ordering = ('structure', 'order')

@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'structure', 'subject', 'ca_total', 'exam_score', 'total_score', 'created_at')
    list_filter = ('structure__branch', 'structure__session', 'structure__term', 'subject')
    search_fields = ('student__first_name', 'student__last_name', 'subject__name')
    ordering = ('student', 'structure', 'subject')

    # Inline for managing component scores directly within the result
    class StudentComponentScoreInline(admin.TabularInline):
        model = StudentComponentScore
        extra = 1  # Number of empty forms displayed
        fields = ('component', 'score')
        ordering = ('component__order',)

    inlines = [StudentComponentScoreInline]

@admin.register(StudentComponentScore)
class StudentComponentScoreAdmin(admin.ModelAdmin):
    list_display = ('result', 'component', 'score')
    list_filter = ('result__structure__branch', 'result__structure__session', 'result__structure__term')
    search_fields = ('result__student__first_name', 'result__student__last_name', 'component__name')
    ordering = ('result', 'component')
