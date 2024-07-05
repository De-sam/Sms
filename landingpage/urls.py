from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home-page'),
    path('about/', views.about, name='about-page'),
    path('contact/', views.contact, name='contact-page'),
    path('features/', views.features, name='features-page'),
    path('pricing/', views.pricing, name='pricing-page'),
    path('registration/', views.registration, name='registration-page'),
]