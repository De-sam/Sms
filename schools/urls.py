from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomPasswordResetConfirmView


urlpatterns = [
    path('<str:short_code>/logout/', views.logout_view, name='logout-view'),
    path('<str:short_code>/login/', views.login, name='login-page'),
    path('<str:short_code>/fprgot-password/', views.forgot_password, name='forgot_password'),
    path('<str:short_code>/dashboard/', views.dashboard, name='schools_dashboard'),
    path('<str:short_code>/school_profile/', views.school_profile, name='school_profile'),
    path('<str:short_code>/edit_sch_profile/', views.edit_sch_profile, name='edit_sch_profile'),
    path('<str:short_code>/edit_pry_profile/', views.edit_pry_profile, name='edit_pry_profile'),
    path('<str:short_code>/add_branch/', views.add_branch, name='add_branch'),
    path('<str:short_code>/add_pry_branch/', views.add_primary_branch, name='add_primary_branch'),
    path('<str:short_code>/branch_list/', views.branch_list, name='branch_list'),
    path('<str:short_code>/add_primary_school/', views.add_primary_school, name='add_primary_school'),
    path('loader/<short_code>/', views.loader, name='loader'),

    # Password Reset URLs
    path(
        '<str:short_code>/reset-password/',
        auth_views.PasswordResetView.as_view(template_name='schools/password_reset_form.html'),
        name='password_reset',
    ),
    path(
        '<str:short_code>/reset-password/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='schools/password_reset_done.html'),
        name='password_reset_done',
    ),
    path('<str:short_code>/reset-password/confirm/<uidb64>/<token>/',
     CustomPasswordResetConfirmView.as_view(),
     name='password_reset_confirm'
     ),
    path(
        '<str:short_code>/reset-password/complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name='schools/password_reset_complete.html'),
        name='password_reset_complete',
    ),
]
