from django.shortcuts import render, redirect
from .forms import SchoolRegistrationForm
from django.contrib import messages
from django.contrib.auth import login
from .utilities import get_local_governments
from django.http import JsonResponse
from django.db import IntegrityError
# from django.core.mail import send_mail

# Define the generate_shortcode function
def generate_shortcode(name):
    words = name.split()
    shortcode = ''.join([word[0] + word[-1] for word in words]).lower()
    return shortcode

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

def register(request):
    if request.method == 'POST':
        form = SchoolRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Generate the shortcode from the school name
                school_name = form.cleaned_data['school_name']
                shortcode = generate_shortcode(school_name)
                form.instance.short_code = shortcode

                # Save the form
                form.save()

                # Send an email to the administrator
                # admin_email = form.cleaned_data['admin_email']
                # subject = 'School Registration Successful'
                # message = f'Dear {form.cleaned_data["admin_first_name"]},\n\nYour school has been successfully registered with the shortcode: {shortcode}.\n\nRegards,\nYour Team'
                # from_email = 'your-email@gmail.com'
                # recipient_list = [admin_email]
                # send_mail(subject, message, from_email, recipient_list, fail_silently=False)

                messages.success(request, 'School registered successfully!.')
                return render(request, 'landingpage/redirect.html', {'title': 'Registration', 'form': form, 'redirect': True, 'shortcode': shortcode})
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

    return render(request, 'landingpage/registration.html', {'title': 'Registration', 'form': form, 'redirect': False})

def get_lgas(request):
    state = request.GET.get('state')
    lgas = get_local_governments().get(state, [])
    return JsonResponse({'lgas': lgas})
