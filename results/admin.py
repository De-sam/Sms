from django.contrib import admin
from .models import ResultStructure, ResultComponent

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
