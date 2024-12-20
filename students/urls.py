from django.urls import path
from . import views

urlpatterns = [
    
    path('<str:short_code>/add-parent/', views.add_parent_guardian, name='add-parent'),
    path('<str:short_code>/add-student/', views.add_student, name='add-student'),
    path('<str:short_code>/edit student/<int:student_id>/', views.edit_student, name='edit_student'),
    path('<str:short_code>/student-list/', views.student_list, name='student_list'),
    path('<str:short_code>/get-classes/<int:branch_id>/', views.get_classes, name='get-classes'),
    path('<str:short_code>/bulk-delete-students/', views.bulk_delete_students, name='bulk_delete_students'),
    path('<str:short_code>/parent-list/', views.list_parent_guardians, name='parent_guardian_list'),
    path('<str:short_code>/edit-parent/<int:parent_id>/', views.edit_parent, name='edit_parent_guardian'),
    path('<str:short_code>/delete-parent/<int:parent_id>/', views.delete_parent, name='delete_parent_guardian'),

]
