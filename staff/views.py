from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import StaffCreationForm
from schools.models import SchoolRegistration
from classes.models import Branch
from django.http import HttpResponse
from .forms import StaffCreationForm

def add_staff(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)
    
    if request.method == 'POST':
        form = StaffCreationForm(request.POST, request.FILES)
        form.fields['branches'].queryset = branches  # Set the filtered branches to the form
        if form.is_valid():
            form.save(school=school)
            return redirect('staff_list', short_code=school.short_code)  # Redirect after successful save
        else:
            print(form.errors)  # Debugging: print any form errors
    else:
        form = StaffCreationForm()
        form.fields['branches'].queryset = branches  # Set the filtered branches to the form during initialization

    return render(request, 'staff/add_staff.html', {
        'form': form,
        'school': school,
    })

