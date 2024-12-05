from django.urls import path
from . import views

urlpatterns = [
    # Create or update result structure
    path('<str:short_code>/create-result-structure/', views.create_result_structure, name='create_result_structure'),

    # Add or update result components for a specific structure
    path('<str:short_code>/add-result-components/<int:structure_id>/', views.add_result_components, name='add_result_components'),
]
