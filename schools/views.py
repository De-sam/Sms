from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as django_login, logout
from django.contrib import messages
from landingpage.models import SchoolRegistration
from schools.models import PrimarySchool,Branch
from .forms import LoginForm,\
SchoolProfileUpdateForm, BranchForm,\
PrimarySchoolForm,PrimaryBranchForm,UpdatePrimarySchoolForm
from django.urls import reverse
from django.db import IntegrityError
from utils.decorator import login_required_with_short_code

def login(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user == school.admin_user:
                    django_login(request, user)
                    next_url = request.GET.get('next', reverse('loader', kwargs={'short_code': short_code}))
                    return redirect(next_url)
                elif hasattr(user, 'staff') and user.staff.branches.filter(school=school).exists():
                    if user.staff.status == 'active':  # Check if the staff member is active
                        django_login(request, user)
                        next_url = request.GET.get('next', reverse('loader', kwargs={'short_code': short_code}))
                        return redirect(next_url)  # Redirect to the school's dashboard
                    else:
                        messages.error(request, 'Your account is inactive. Please contact the administrator.')
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

def loader(request, short_code):
    return render(request, 'schools/loader.html', {'short_code': short_code})

def logout_view(request, short_code):
    logout(request)
    messages.success(request, 'logged out sucessfully!!!.')
    return redirect('login-page', short_code=short_code)

@login_required_with_short_code
def dashboard(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
   # Count branches directly associated with the school (secondary branches)
    secondary_school_branches_count = Branch.objects.filter(school=school).count()

    # Fetch branches associated with the secondary school
    secondary_school_branches = Branch.objects.filter(school=school).exclude(primary_school__isnull=False)
    secondary_school_branches_count = secondary_school_branches.count()

    # Fetch primary schools associated with the secondary school
    primary_schools = PrimarySchool.objects.filter(parent_school=school)

    # Fetch branches associated with all primary schools
    primary_school_branches = Branch.objects.filter(primary_school__in=primary_schools)
    primary_school_branches_count = primary_school_branches.count()

    # Total branches
    total_branches = secondary_school_branches_count + primary_school_branches_count
    
    context = {
        'number_of_branches': total_branches,
        'number_of_students': 500,
        'number_of_teachers': 25,
        'total_attendance': 4500,
        'Placeholder_title': 'Sample Title',
        'school':school
        # Add other context variables as needed
    }
    return render(request, 'schools/base_dash.html', context)

@login_required_with_short_code
def school_profile(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    try:
        # Attempt to get the PrimarySchool instance
        primary_school = PrimarySchool.objects.get(parent_school=school)
    except PrimarySchool.DoesNotExist:
        primary_school = []

    return render(request, "schools/school_profile.html", {
        'school': school,
        'pry_school': primary_school,
    })

@login_required_with_short_code
def edit_sch_profile(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = SchoolProfileUpdateForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, 'School profile updated successfully!')
            return redirect('edit_sch_profile', short_code=short_code)
    else:
        form = SchoolProfileUpdateForm(instance=school)

    return render(request, "schools/edit_sch_profile.html", {'school': school, 'form': form})

@login_required_with_short_code
def edit_pry_profile(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    try:
        # Attempt to get the PrimarySchool instance associated with the SchoolRegistration
        primary_school = PrimarySchool.objects.get(parent_school=school)
    except PrimarySchool.DoesNotExist:
        # Handle the case where no PrimarySchool is found
        messages.error(request, 'No primary school found for the selected school.')
        return redirect('school_profile', short_code=short_code)

    if request.method == 'POST':
        form = UpdatePrimarySchoolForm(request.POST, request.FILES, instance=primary_school)
        if form.is_valid():
            form.save()
            messages.success(request, 'School profile updated successfully!')
            return redirect('school_profile', short_code=short_code)
    else:
        form = UpdatePrimarySchoolForm(instance=primary_school)

    return render(request, "schools/edit_pry_profile.html",
                {'school': school,
                'form': form,
                'pry_school':primary_school
                })


@login_required_with_short_code
def add_branch(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.school = school
            branch.save()
            messages.success(request, 'Branch added successfully!')
            return redirect('school_profile', short_code=short_code)
    else:
        form = BranchForm()

    return render(request, 'schools/add_branch.html', {'form': form, 'school': school})

@login_required_with_short_code
def add_primary_branch(request, short_code):
    # Get the SchoolRegistration instance for the provided short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    try:
        # Attempt to get the PrimarySchool instance associated with the SchoolRegistration
        primary_school = PrimarySchool.objects.get(parent_school=school)
    except PrimarySchool.DoesNotExist:
        # Handle the case where no PrimarySchool is found
        messages.error(request, 'No primary school found for the selected school.')
        return redirect('school_profile', short_code=short_code)

    if request.method == 'POST':
        form = PrimaryBranchForm(request.POST)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.school = school
            branch.primary_school = primary_school
            branch.save()
            messages.success(request, 'Branch added successfully!')
            return redirect('branch_list', short_code=short_code)
    else:
        form = PrimaryBranchForm()

    return render(request, 'schools/add_pry_branch.html', {
        'form': form,
        'school': school,
        'primary_school': primary_school
    })


@login_required_with_short_code
def branch_list(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Fetch branches associated with the general school
    secondary_school_branches = Branch.objects.filter(school=school).exclude(primary_school__isnull=False)
    
    # Fetch  primary schools associated with school
    try:
        # Attempt to get the PrimarySchool instance
        primary_school = PrimarySchool.objects.get(parent_school=school)
    except PrimarySchool.DoesNotExist:
        primary_school = []

    # Fetch branches associated with primary schools
    primary_school_branches = Branch.objects.filter(primary_school__isnull=False, primary_school__parent_school=school)

    return render(request, 'schools/branch_list.html',{
        'school': school,
        'pry_sch': primary_school,
        'sec_sch_branches': secondary_school_branches,
        'pry_sch_branches': primary_school_branches,
    })

@login_required_with_short_code
def add_primary_school(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = PrimarySchoolForm(request.POST, request.FILES)
        if form.is_valid():
            primary_school = form.save(commit=False)
            primary_school.admin_user = request.user  # Ensure admin_user is set
            primary_school.school_id = school.school_id
            primary_school.parent_school = school 

            try:
                primary_school.save()
                messages.success(request, 'Primary section added successfully!')
                return redirect ( 'school_profile', short_code=short_code )
            except IntegrityError:
                # Handle the case where the unique constraint fails
                messages.error(request, 'A primary school already exists for this secondary school. Please check and try again.')
                return render(request, 'schools/add_primary_school.html', {'form': form, 'school': school})
    else:
        form = PrimarySchoolForm()

    return render(request, 'schools/add_primary_school.html', {'form': form, 'school': school})