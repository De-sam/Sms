from django.urls import path
from . import views

urlpatterns = [
    path('<str:short_code>/create-session/', views.create_session, name='create_session'),
    path('<str:short_code>/edit-session/<int:pk>/', views.edit_session, name='edit_session'),
    path('<str:short_code>/add-term/<int:session_id>/', views.add_term, name='add_term'),
    path('<str:short_code>/edit-term/<int:pk>/', views.edit_term, name='edit_term'),
    path('<str:short_code>/list-sessions/', views.list_sessions, name='list_sessions'),
    path('<str:short_code>/list-terms/<int:session_id>/', views.list_terms, name='list_terms'),
    # Add more URLs as needed
]
