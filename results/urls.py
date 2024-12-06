from django.urls import path
from . import views
from utils.academics import *

urlpatterns = [
    # Create or update result structure
    path('<str:short_code>/create-result-structure/', views.create_result_structure, name='create_result_structure'),

    path('<str:short_code>/list-result-structures/', views.list_result_structures, name='list_result_structures'),

    # Add or update result components for a specific structure
    path('<str:short_code>/add-result-components/<int:structure_id>/', views.add_result_components, name='add_result_components'),

    path('<str:short_code>/get-sessions/', get_sessions, name='get_sessions'),
    path('<str:short_code>/get-terms/<int:session_id>/', get_terms, name='get_terms'),
    path('<str:short_code>/get-branches/', get_branches, name='get_branches'),
    path('<str:short_code>/get-classes/<int:branch_id>/', get_classes_by_branch, name='get_classes_by_branch'),
]
