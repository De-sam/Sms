from django.urls import path
from . import views

urlpatterns = [
    path('<str:short_code>/add-staff/', views.add_staff, name='add_staff'),
    path('<str:short_code>/staff-list/', views.staff_list, name='staff_list'),
    path('<str:short_code>/edit-staff/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('<str:short_code>/delete-staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('<str:short_code>/assign-subjects/<int:staff_id>/', views.assign_subjects_to_staff, name='assign_subjects_to_staff'),
    # Other URLs...
]