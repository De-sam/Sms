from django.contrib import admin
from .models import PsychomotorRating, BehavioralRating

@admin.register(PsychomotorRating)
class PsychomotorRatingAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'term', 'branch', 'rating_date', 'coordination', 'handwriting', 'sports', 'music')
    search_fields = ('student__first_name', 'student__last_name', 'session__session_name', 'term__term_name', 'branch__branch_name')
    list_filter = ('session', 'term', 'branch', 'rating_date')

    def student_full_name(self, obj):
        return obj.student.full_name()
    student_full_name.short_description = 'Student'

@admin.register(BehavioralRating)
class BehavioralRatingAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'term', 'branch', 'rating_date', 'punctuality', 'attentiveness', 'obedience', 'leadership')
    search_fields = ('student__first_name', 'student__last_name', 'session__session_name', 'term__term_name', 'branch__branch_name')
    list_filter = ('session', 'term', 'branch', 'rating_date')

    def student_full_name(self, obj):
        return obj.student.full_name()
    student_full_name.short_description = 'Student'
