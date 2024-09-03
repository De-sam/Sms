from django.urls import path
from . import views

urlpatterns = [
    path('<str:short_code>/add-staff/', views.add_staff, name='add_staff'),
    path('<str:short_code>/staff-list/', views.staff_list, name='staff_list'),
    path('<str:short_code>/edit-staff/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('<str:short_code>/delete-staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('<str:short_code>/assign-subjects/<int:staff_id>/', views.assign_subjects_to_staff, name='assign_subjects_to_staff'),
    path('<str:short_code>/assignments/', views.teacher_assignments_view, name='teacher_assignments'),
    path('<str:short_code>/upload_staff/', views.upload_staff, name='upload_staff'),
    path('<str:short_code>/download_staff_template/', views.download_staff_template, name='download_staff_template'),
    # Other URLs...
]
