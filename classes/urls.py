from django.urls import path
from . import views


urlpatterns = [
    path('<short_code>/assign_primary_classes', views.assign_classes_primary, name='assign_classes_primary'),
    path('<short_code>/assign_condary_classes', views.assign_classes_secondary, name='assign_classes_secondary'),
    path('<short_code>/add_class_primary', views.add_class_primary, name='add_class_primary'),
    path('<short_code>/add_class_secondary', views.add_class_secondary, name='add_class_secondary'),
    path('<short_code>/primary_school_classes', views.primary_school_classes, name='primary_school_classes'),
    path('<short_code>/secondary_school_classes', views.secondary_school_classes, name='secondary_school_classes'),
    # Add other URL patterns# Add other school-specific URLs here
]
