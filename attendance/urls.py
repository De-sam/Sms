from django.urls import path
from . import views
from utils.academics import get_sessions, get_terms, get_classes_by_branch, get_branches

urlpatterns = [
    # New URL pattern for setting school days open
    path('<short_code>/set-school-days-open/', views.set_school_days_open, name='set_school_days_open'),
    
    # URL pattern for getting sessions for a given school identified by short_code
    path('<str:short_code>/get-sessions/', get_sessions, name='get_sessions'),
    
    # URL pattern for getting terms for a given session under a school
    path('<str:short_code>/get-terms/<int:session_id>/', get_terms, name='get_terms'),
    
    # URL for getting branches for a given school
    path('<str:short_code>/get-branches/', get_branches, name='get_branches'),
    
    # URL for getting classes for a given branch under a school
    path('<str:short_code>/get-classes/<int:branch_id>/', get_classes_by_branch, name='get_classes_by_branch'),
    
    # URL for recording student attendance
    path('<str:short_code>/student-attendance/', views.record_student_attendance, name='record_student_attendance'),

    path('<str:short_code>/get-attendance/', views.get_attendance, name='get_attendance'),
]
