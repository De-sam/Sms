from django.urls import path
from . import views

urlpatterns = [
    path('<str:short_code>/add-parents/', views.add_parent_guardian, name='add-parents'),
    path('<str:short_code>/add-student/', views.add_student, name='add_student'),
    # path('<str:short_code>/edit student/<int:student_id>/', views.edit_student, name='edit_student'),
    path('<str:short_code>/student-list/', views.student_list, name='student_list'),


]
