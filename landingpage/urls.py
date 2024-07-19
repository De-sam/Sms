from django.urls import path
from . import views
from .views import  get_lgas




urlpatterns = [
    path('', views.home, name='home-page'),
    path('about/', views.about, name='about-page'),
    path('contact/', views.contact, name='contact-page'),
    path('features/', views.features, name='features-page'),
    path('pricing/', views.pricing, name='pricing-page'),
    path('register/', views.register, name='registration-page'),
    path('redirect/', views.redirect, name='redirect-page'),
    path('get-lgas/', get_lgas, name='get_lgas'),
]