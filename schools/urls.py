from django.urls import path
from . import views


urlpatterns = [
    path('<str:short_code>/logout/', views.logout_view, name='logout-view'),
    path('<str:short_code>/login/', views.login, name='login-page'),
    path('<str:short_code>/dashboard/', views.dashboard, name='schools_dashboard'),
    path('<str:short_code>/school_profile/', views.school_profile, name='school_profile'),
    path('<str:short_code>/edit_sch_profile/', views.edit_sch_profile, name='edit_sch_profile'),
    path('<str:short_code>/add_branch/', views.add_branch, name='add_branch'),
     path('<str:short_code>/add_primary_school/', views.add_primary_school, name='add_primary_school'),
    path('loader/<short_code>/', views.loader, name='loader'),
    # Add other school-specific URLs here
]
