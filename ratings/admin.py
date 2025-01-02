from django.contrib import admin
from .models import RatingCriteria, Rating


@admin.register(RatingCriteria)
class RatingCriteriaAdmin(admin.ModelAdmin):
    list_display = ('criteria_name', 'rating_type', 'branch', 'school', 'max_value')
    list_filter = ('rating_type', 'branch', 'school')
    search_fields = ('criteria_name', 'school__school_name', 'branch__branch_name')
    ordering = ('school', 'branch', 'rating_type', 'criteria_name')
    readonly_fields = ('id',)
    list_per_page = 20


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('student', 'criteria', 'value', 'session', 'term', 'branch', 'rating_type', 'rating_date')
    list_filter = ('session', 'term', 'branch', 'rating_type')
    search_fields = ('student__first_name', 'student__last_name', 'criteria__criteria_name', 'branch__branch_name')
    ordering = ('session', 'term', 'branch', 'rating_type', 'student')
    readonly_fields = ('id', 'rating_date')
    list_per_page = 20
