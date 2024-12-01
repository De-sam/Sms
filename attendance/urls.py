from django.urls import path
from . import views
from utils.academics import get_sessions, get_terms

urlpatterns = [
    # New URL pattern for setting school days open
    path('<short_code>/set-school-days-open/', views.set_school_days_open, name='set_school_days_open'),
    # URL pattern for getting sessions for a given school identified by short_code
    path('<str:short_code>/get-sessions/', get_sessions, name='get_sessions'),
    # URL pattern for getting terms for a given session under a school
    path('<str:short_code>/get-terms/<int:session_id>/', get_terms, name='get_terms'),
]
