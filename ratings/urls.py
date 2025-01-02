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

    # URL for managing rating criteria
    path('<str:short_code>/manage-rating-criteria/', views.manage_rating_criteria, name='manage_rating_criteria'),

    # URL for managing ratings
    path('<str:short_code>/manage-ratings/', views.manage_ratings, name='manage_ratings'),

    # URL to fetch students and criteria for ratings
    path('<str:short_code>/fetch-students-and-criteria/', views.fetch_students_and_criteria, name='fetch_students_and_criteria'),

    # URL for saving ratings
    path('<str:short_code>/save-ratings/', views.save_ratings, name='save_ratings'),
]
