from django.urls import path
from . import views

urlpatterns = [
    path('fetch_account_name', views.fetch_account_name, name='fetch_account_name'), 
    path('<str:short_code>/account/verify/', views.fetch_account_name, name='fetch_account_name'),
    path('<str:short_code>/assign-classes/<int:teacher_id>/', views.assign_teacher_to_class, name='assign_teacher_to_class'),
    path('<str:short_code>/get-classes-by-branch/<int:branch_id>/', views.get_classes_by_branch, name='get_classes_by_branch'),
    path('<str:short_code>/get-sessions/', views.get_sessions, name='get_sessions'),
    path('<str:short_code>/get-terms/<int:session_id>/', views.get_terms, name='get_terms'),
    path('<str:short_code>/get-classes-by-subject/<int:branch_id>/<int:subject_id>/', views.get_classes_by_subject, name='get_classes_by_subject'),    path('<str:short_code>/get-classes/<int:branch_id>/<int:subject_id>/', views.get_classes, name='get_classes'),
    path('<str:short_code>/get-subjects-and-classes/<int:branch_id>/', views.get_subjects_and_classes, name='get_subjects_and_classes'),
    path('<str:short_code>/pre-add-staff/', views.pre_add_staff, name='pre_add_staff'),
    path('<str:short_code>/add-staff/', views.add_staff, name='add_staff'),
    path('<str:short_code>/staff-list/', views.staff_list, name='staff_list'),
    path('<str:short_code>/edit-staff/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('<str:short_code>/delete-staff/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('<str:short_code>/assign-subjects/<int:staff_id>/', views.assign_subjects_to_staff, name='assign_subjects_to_staff'),
    path('<str:short_code>/assignments/', views.teacher_assignments_view, name='teacher_assignments'),
    path('<str:short_code>/upload_staff/', views.upload_staff, name='upload_staff'),
    path('<str:short_code>/download_staff_template/', views.download_staff_template, name='download_staff_template'),
    path('<str:short_code>/copy-term-assignments/', views.copy_term_assignments, name='copy_term_assignments'),
    path('<str:short_code>/copy-session-assignments/', views.copy_session_assignments, name='copy_session_assignments'),
    path('<str:short_code>/employment-letter/<int:staff_id>/', views.generate_employment_letter, name='employment_letter'),
    # Other URLs...
]
