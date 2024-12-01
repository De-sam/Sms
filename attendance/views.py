from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction, IntegrityError
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
    # Get the school and its branches
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)

    if request.method == 'POST':
        form = SchoolDaysOpenForm(request.POST)
        form.fields['branches'].queryset = branches  # Ensure branches are unique to the current school

        if form.is_valid():
            # Extract cleaned data
            session = form.cleaned_data['session']
            term = form.cleaned_data['term']
            branches = form.cleaned_data['branches']
            days_open = form.cleaned_data['days_open']
            
            try:
                # Loop through each selected branch and create/update SchoolDaysOpen records
                for branch in branches:
                    school_days_open, created = SchoolDaysOpen.objects.update_or_create(
                        branch=branch,
                        session=session,
                        term=term,
                        defaults={'days_open': days_open}
                    )

                # Success message after setting school days open successfully
                messages.success(request, f'School days open set successfully for {session.session_name}, {term.term_name}!')
                return redirect('set_school_days_open', short_code=short_code)

            except IntegrityError:
                # Handle duplicate entry attempts by displaying an error message
                messages.error(request, f'An entry for {session.session_name}, {term.term_name} already exists for one of the selected branches. Please update the existing entry instead.')
    
    else:
        # Initialize an empty form and limit branches to the current school
        form = SchoolDaysOpenForm()
        form.fields['branches'].queryset = branches

    # Render the template for setting school days open
    return render(request, 'attendance/set_school_days_open.html', {
        'form': form,
        'school': school,
    })
