from django.urls import path
from . import views
from utils.academics import *


urlpatterns = [
    # Admin-Specific Views
    path('<str:short_code>/filter-comments/', views.filter_students_for_comments, name='filter_comments'),
    path('<str:short_code>/get-comments/', views.get_comments, name='get_comments'),
    path('<str:short_code>/save-comments/', views.save_comments, name='save_comments'),

    # Utility Endpoints for Filtering
    path('<str:short_code>/get-sessions/', get_sessions, name='get_sessions'),
    path('<str:short_code>/get-terms/<int:session_id>/', get_terms, name='get_terms'),
    path('<str:short_code>/get-branches/', get_branches, name='get_branches'),
    path('<str:short_code>/get-classes/<int:branch_id>/', get_classes_by_branch, name='get_classes_by_branch'),
]
