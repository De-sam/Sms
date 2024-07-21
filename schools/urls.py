from django.urls import path
from . import views


urlpatterns = [
    path('<str:short_code>/login/', views.login, name='login-page'),
    path('<str:short_code>/dashboard/', views.dashboard, name='dashboard'),
     path('loader/<short_code>/', views.loader, name='loader'),
    # Add other school-specific URLs here
]
