from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from academics.models import Session, Term
from schools.models import Branch
from landingpage.models import SchoolRegistration
from .models import SchoolDaysOpen
from .forms import SchoolDaysOpenForm
from utils.decorator import login_required_with_short_code
from utils.permissions import admin_required

@login_required_with_short_code
@admin_required
@transaction.atomic
def set_school_days_open(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    if request.method == 'POST':
        form = SchoolDaysOpenForm(request.POST)
        if form.is_valid():
            session = form.cleaned_data['session']
            term = form.cleaned_data['term']
            branches = form.cleaned_data['branches']
            days_open = form.cleaned_data['days_open']
            
            for branch in branches:
                # Create or update the number of days for each branch
                school_days_open, created = SchoolDaysOpen.objects.update_or_create(
                    branch=branch,
                    session=session,
                    term=term,
                    defaults={'days_open': days_open}
                )
            
            messages.success(request, f'School days open set successfully for {session.session_name}, {term.term_name}!')
            return redirect('set_school_days_open', short_code=short_code)
    else:
        form = SchoolDaysOpenForm()

    return render(request, 'attendance/set_school_days_open.html', {
        'form': form,
        'school': school,
    })
