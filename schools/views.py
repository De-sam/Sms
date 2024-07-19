from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as django_login
from django.contrib import messages
from landingpage.models import SchoolRegistration
from .forms import LoginForm
from django.contrib.auth.decorators import login_required

def login(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Verify if the user is the admin of the school
                if user == school.admin_user:
                    django_login(request, user)
                    return redirect('dashboard',  short_code=short_code)  # Adjust to your dashboard URL
                else:
                    messages.error(request, 'You are not authorized to log in for this school.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    context = {
        'school': school,
        'title': f'{school.school_name} Login',
        'form': form,
    }
    
    return render(request, 'schools/login.html', context)

@login_required
def dashboard(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Add additional logic for the dashboard here
    return render(request, 'schools/dashboard.html', {'school': school})