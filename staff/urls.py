from django.urls import path
from . import views

urlpatterns = [
    path('<str:short_code>/add-staff/', views.add_staff, name='add_staff'),
    # Other URLs...
]
