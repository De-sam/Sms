from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as django_login, logout
from django.contrib import messages
from landingpage.models import SchoolRegistration
from schools.models import PrimarySchool, Branch
from .forms import (
    LoginForm,
    SchoolProfileUpdateForm,
    BranchForm,
    PrimarySchoolForm,
    PrimaryBranchForm,
    UpdatePrimarySchoolForm,
)
from django.urls import reverse
from django.db import IntegrityError
from utils.decorator import login_required_with_short_code
from students.models import ParentStudentRelationship, Student, ParentGuardian
from staff.models import Staff
from django.db.models import Case, When, Value, CharField, Count, Subquery, OuterRef  # Corrected this import
from django.core.serializers.json import DjangoJSONEncoder
import json

def login(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Admin user
                if user == school.admin_user:
                    django_login(request, user)
                    next_url = request.GET.get('next', reverse('loader', kwargs={'short_code': short_code}))
                    return redirect(next_url)

                # Staff member
                elif hasattr(user, 'staff') and user.staff.branches.filter(school=school).exists():
                    if user.staff.status == 'active':  # Ensure staff member is active
                        django_login(request, user)
                        next_url = request.GET.get('next', reverse('loader', kwargs={'short_code': short_code}))
                        return redirect(next_url)
                    else:
                        messages.error(request, 'Your account is inactive. Please contact the administrator.')

                # Student
                elif hasattr(user, 'student_profile') and user.student_profile.branch.school == school:
                    django_login(request, user)
                    next_url = request.GET.get('next', reverse('loader', kwargs={'short_code': short_code}))
                    return redirect(next_url)

                # Parent
                elif hasattr(user, 'parent_profile'):  # Using `parent_profile` based on the related_name
                    # Verify parent has students in the specific school
                    if ParentStudentRelationship.objects.filter(
                        parent_guardian=user.parent_profile, 
                        student__branch__school=school
                    ).exists():
                        django_login(request, user)
                        next_url = request.GET.get('next', reverse('loader', kwargs={'short_code': short_code}))
                        return redirect(next_url)
                    else:
                        messages.error(request, 'No students associated with your account in this school.')
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
    user = request.user

     # Determine user roles
    is_school_admin = user == school.admin_user
    is_teacher = hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher'
    is_student = hasattr(user, 'student_profile') and user.student_profile.branch.school == school
    is_parent = hasattr(user, 'parent_profile') and ParentStudentRelationship.objects.filter(
        parent_guardian=user.parent_profile,
        student__branch__school=school
    ).exists()

    # Number of branches
    number_of_branches = Branch.objects.filter(school=school).count()
    print(f"Number of Branches: {number_of_branches}")

    # Number of students
    number_of_students = Student.objects.filter(branch__school=school).count()
    print(f"Number of Students: {number_of_students}")

    # Number of staff
    number_of_staff = Staff.objects.filter(branches__school=school).distinct().count()
    print(f"Number of Staff: {number_of_staff}")

    # Number of parents
    number_of_parents = ParentGuardian.objects.filter(school=school).count()
    print(f"Number of Parents: {number_of_parents}")

    # Data for branch distribution chart
    branch_distribution = (
        Branch.objects.filter(school=school)
        .annotate(
            branch_type=Case(
                When(primary_school__isnull=True, then=Value("College")),
                When(primary_school__isnull=False, then=Value("Primary")),
                output_field=CharField(),
            ),
            student_count=Subquery(
                Student.objects.filter(branch_id=OuterRef('id'))
                .values('branch_id')
                .annotate(count=Count('id'))
                .values('count')[:1]
            )
        )
        .values('branch_name', 'branch_type', 'student_count')
    )

    branch_labels = [
        f"{branch['branch_name']} ({branch['branch_type']})" for branch in branch_distribution
    ]
    branch_data = [int(branch['student_count'] or 0) for branch in branch_distribution]

    print(f"Branch Labels: {branch_labels}")
    print(f"Branch Data: {branch_data}")

    context = {
        'school': school,
        'number_of_branches': number_of_branches,
        'number_of_students': number_of_students,
        'number_of_staff': number_of_staff,
        'number_of_parents': number_of_parents,
        'branch_labels_json': json.dumps(branch_labels, cls=DjangoJSONEncoder),
        'branch_data_json': json.dumps(branch_data, cls=DjangoJSONEncoder),
        'is_school_admin': is_school_admin,
        'is_teacher': is_teacher,
        'is_student': is_student,
        'is_parent': is_parent,
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