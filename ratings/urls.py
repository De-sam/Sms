from django.urls import path
from . import views
from utils.academics import *

urlpatterns = [
    # URL pattern for getting sessions for a given school identified by short_code
    path('<str:short_code>/get-sessions/', get_sessions, name='get_sessions'),

    # URL pattern for getting terms for a given session under a school
    path('<str:short_code>/get-terms/<int:session_id>/', get_terms, name='get_terms'),

    # URL for getting branches for a given school
    path('<str:short_code>/get-branches/', get_branches, name='get_branches'),

    # URL for getting classes for a given branch under a school
    path('<str:short_code>/get-classes/<int:branch_id>/', get_classes_by_branch, name='get_classes_by_branch'),

    # Filter Ratings
    path('<str:short_code>/filter-ratings/', views.filter_students_for_ratings, name='filter_ratings'),

    # Get Ratings (JSON response for filtered students)
    path('<str:short_code>/get-ratings/', views.get_ratings, name='get_ratings'),

    # Save Ratings (save submitted ratings data)
    path('<str:short_code>/save-ratings/', views.save_ratings, name='save_ratings'),
]
