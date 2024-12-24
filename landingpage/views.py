import uuid
from .models import SchoolRegistration
from django.shortcuts import render, redirect
from .forms import SchoolRegistrationForm
from django.contrib import messages
from django.contrib.auth import login
from .utilities import get_local_governments
from django.http import JsonResponse
from django.db import IntegrityError
from django.core.mail import send_mail

def home(request):
    return render(request, 'landingpage/home.html', {'title': 'Home'})

def about(request):
    return render(request, 'landingpage/about.html', {'title': 'About'})

def contact(request):
    return render(request, 'landingpage/contact.html', {'title': 'Contact'})

def features(request):
    return render(request, 'landingpage/features.html', {'title': 'Features'})

def pricing(request):
    return render(request, 'landingpage/pricing.html', {'title': 'Pricing'})

def send_registration_email(request, school_name, admin_email, first_name, shortcode):
    subject = 'School Registration Successful'
    login_url = f'http://sms-lme5.onrender.com/schools/{shortcode}/login/'
    message = (
        f'Dear {first_name},\n\n'
        f'Your school "{school_name}" has been successfully registered. '
        f'You can visit this link to log in: {login_url}\n\n'
        f'Regards,\nYour Team'
    )
    from_email = 'admin@example.com'
    recipient_list = [admin_email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    except Exception as e:
        print(f"Failed to send registration email: {e}")
        messages.error(request, 'Registration email could not be sent. Please check your email settings.')

def register(request):
    if request.method == 'POST':
        form = SchoolRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                school_name = form.cleaned_data['school_name']
                shortcode = SchoolRegistration.generate_shortcode(school_name)
                form.instance.short_code = shortcode

                form.save()

                first_name = form.cleaned_data['first_name']
                admin_email = form.cleaned_data['email']
                send_registration_email(request, school_name, admin_email, first_name, shortcode)

                return render(request, 'landingpage/redirect.html', {
                    'title': 'Registration',
                    'form': form,
                    'redirect': True,
                    'shortcode': shortcode
                })

            except IntegrityError as e:
                if 'unique constraint' in str(e).lower():
                    form.add_error('admin_email', 'A school with this admin email already exists.')
                else:
                    form.add_error(None, 'An error occurred. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SchoolRegistrationForm()

    if 'state' in request.GET:
        state = request.GET.get('state')
        local_governments = get_local_governments().get(state, [])
        form.fields['lga'].choices = [(lg, lg) for lg in local_governments]

    return render(request, 'landingpage/registration.html', {'title': 'Registration', 'form': form})

def get_lgas(request):
    state = request.GET.get('state')
    lgas = get_local_governments().get(state, [])
    return JsonResponse({'lgas': lgas})
