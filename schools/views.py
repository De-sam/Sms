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
from utils.permissions import admin_required,teacher_required
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

    # Determine user roles exclusively
    is_school_admin = user == school.admin_user
    is_teacher = False
    is_student = False
    is_parent = False
    is_accountant = False

    if not is_school_admin:
        if hasattr(user, 'staff'):
            if user.staff.role.name.lower() == 'teacher':
                is_teacher = True
            elif user.staff.role.name.lower() == 'accountant':
                is_accountant = True
        elif hasattr(user, 'student_profile') and user.student_profile.branch.school == school:
            is_student = True
        elif hasattr(user, 'parent_profile') and ParentStudentRelationship.objects.filter(
            parent_guardian=user.parent_profile,
            student__branch__school=school
        ).exists():
            is_parent = True

    # Base context for all roles #
    context = {
        'school': school,
        'is_school_admin': is_school_admin,
        'is_teacher': is_teacher,
        'is_student': is_student,
        'is_parent': is_parent,
        'is_accountant': is_accountant,
    }

################## Add admin-specific data #################################
    if is_school_admin:
        number_of_branches = Branch.objects.filter(school=school).count()
        number_of_students = Student.objects.filter(branch__school=school).count()
        number_of_staff = Staff.objects.filter(branches__school=school).distinct().count()
        number_of_parents = ParentGuardian.objects.filter(school=school).count()

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

        # Add admin-specific context
        context.update({
            'number_of_branches': number_of_branches,
            'number_of_students': number_of_students,
            'number_of_staff': number_of_staff,
            'number_of_parents': number_of_parents,
            'branch_labels_json': json.dumps(branch_labels, cls=DjangoJSONEncoder),
            'branch_data_json': json.dumps(branch_data, cls=DjangoJSONEncoder),
        })

################################ Add teacher-specific data #######################################################
    if is_teacher:
        # Example: Add a list of classes the teacher is assigned to
        teacher_classes = []  # Assuming there's a related name `classes`
        context.update({
            'teacher_classes': teacher_classes,
            'assignments_due': [],  # Placeholder for teacher-specific data like assignments
        })

######################## Add student-specific data #########################################
    if is_student:
        # Example: Add student-specific information like grades, attendance, and assignments
        student_profile = []
        student_attendance = []  # Placeholder for attendance records
        student_grades = []  # Placeholder for student's grades
        student_assignments = []  # Placeholder for upcoming assignments

        context.update({
            'student_profile': student_profile,
            'student_attendance': student_attendance,
            'student_grades': student_grades,
            'student_assignments': student_assignments,
        })

####################### Add parent-specific data ################################
    if is_parent:
        # Example: Add a list of students related to the parent
        parent_students = ParentStudentRelationship.objects.filter(parent_guardian=user.parent_profile).select_related('student')
        context.update({
            'parent_students': parent_students,
            'parent_notifications': [],  # Placeholder for parent notifications
        })

######################### Add accountant-specific data ########################
    if is_accountant:
        # Example: Add financial information
        financial_reports = []  # Placeholder for financial reports
        context.update({
            'financial_reports': financial_reports,
        })

    return render(request, 'schools/base_dash.html', context)

@login_required_with_short_code
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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