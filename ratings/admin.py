from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = (
        'student', 
        'rating_type', 
        'session', 
        'term', 
        'branch', 
        'rating_date'
    )
    list_filter = (
        'rating_type', 
        'session', 
        'term', 
        'branch', 
        'rating_date'
    )
    search_fields = (
        'student__first_name', 
        'student__last_name', 
        'session__session_name', 
        'term__term_name', 
        'branch__name'
    )
    ordering = ('-rating_date',)  # Newest ratings first

    def get_fields(self, request, obj=None):
        """
        Dynamically adjust fields based on the rating type.
        """
        if obj and obj.rating_type == 'psychomotor':
            return ('student', 'rating_type', 'session', 'term', 'branch',
                    'coordination', 'handwriting', 'sports', 'artistry', 
                    'verbal_fluency', 'games', 'rating_date')
        elif obj and obj.rating_type == 'behavioral':
            return ('student', 'rating_type', 'session', 'term', 'branch',
                    'punctuality', 'attentiveness', 'obedience', 
                    'leadership', 'emotional_stability', 'teamwork', 'rating_date')
        return super().get_fields(request, obj)

    def get_readonly_fields(self, request, obj=None):
        """
        Make `rating_type` and `rating_date` readonly after creation.
        """
        if obj:
            return ('rating_type', 'rating_date')
        return ('rating_date',)

    def save_model(self, request, obj, form, change):
        """
        Add custom save behavior if needed (e.g., validation, notifications).
        """
        # Example: Ensure only relevant fields are filled
        if obj.rating_type == 'psychomotor' and any(
            getattr(obj, field) is not None for field in 
            ['punctuality', 'attentiveness', 'obedience', 
             'leadership', 'emotional_stability', 'teamwork']
        ):
            raise ValueError("Behavioral fields should not be filled for psychomotor ratings.")
      
