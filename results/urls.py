from django.urls import path
from . import views
from utils.academics import *

urlpatterns = [
    # Create or update result structure
    path('<str:short_code>/create-result-structure/', views.create_result_structure, name='create_result_structure'),
    path('<str:short_code>/list-result-structures/', views.list_result_structures, name='list_result_structures'),
    path('<str:short_code>/edit-result-structure/<int:structure_id>/', views.edit_result_structure, name='edit_result_structure'),
    path('<str:short_code>/filter-scores/', views.filter_students_for_scores, name='filter_scores'),

    # Add or update result components for a specific structure
    path('<str:short_code>/add-result-components/<int:structure_id>/', views.add_result_components, name='add_result_components'),

    # Fetch data
    path('<str:short_code>/get-sessions/', get_sessions, name='get_sessions'),
    path('<str:short_code>/get-terms/<int:session_id>/', get_terms, name='get_terms'),
    path('<str:short_code>/get-branches/', get_branches, name='get_branches'),
    path('<str:short_code>/get-classes/<int:branch_id>/', get_classes_by_branch, name='get_classes_by_branch'),
    path('<str:short_code>/get-subjects/<int:branch_id>/', get_subjects_by_branch, name='get_subjects_by_branch'),
    path('<str:short_code>/get-classes/<int:branch_id>/<int:subject_id>/', get_classes_by_subject, name='get_classes_by_subject'),
    path("<str:short_code>/class-result-preview/", views.render_class_result_preview, name="class_result_preview"),
    path("<str:short_code>/fetch-class-results/", views.fetch_class_results, name="fetch_class_results"),
    path('<str:short_code>/publish-result/', views.publish_results, name='publish_results'),
    path('<str:short_code>/list-published-results', views.list_published_results, name='list_published_results'),

    # Fetch and save scores
    path('<str:short_code>/get-student-scores/', views.get_student_scores, name='get_student_scores'),
    path('<str:short_code>/save-student-scores/', views.save_student_scores, name='save_student_scores'),

    # Fetch and display detailed student results
    path('<str:short_code>/generate-result-filter/', views.render_generate_result_filter, name='generate_result_filter'),
    path('<str:short_code>/fetch-students-result/', views.fetch_results_wrapper, name='fetch_students_result'),
    path('<str:short_code>/fetch-students-broadsheet/', views.fetch_results_wrapper, name='fetch_students_broadsheet'),


    # Grading System
    path('<str:short_code>/grading-systems/', views.manage_grading_system, name='manage_grading_system'),
    # path('<str:short_code>/grading-system-data/<int:branch_id>/', views.fetch_grading_system_data, name='fetch_grading_system_data'),
]
