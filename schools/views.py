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


from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User


from students.models import Student
from staff.models import Staff
from students.models import ParentGuardian

from django.contrib.auth.views import PasswordResetConfirmView
from django.shortcuts import get_object_or_404
from landingpage.models import SchoolRegistration
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from datetime import datetime, timedelta
from utils.tokens import CustomPasswordResetTokenGenerator

custom_token_generator = CustomPasswordResetTokenGenerator()


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


class CustomPasswordResetConfirmView(View):
    template_name = 'schools/password_reset_confirm.html'

    def get(self, request, short_code, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and custom_token_generator.check_token(user, token):
            context = {
                'validlink': True,
                'short_code': short_code,
                'uidb64': uidb64,
                'token': token,
                'school': get_object_or_404(SchoolRegistration, short_code=short_code),
            }
            return render(request, self.template_name, context)
        else:
            messages.error(request, "The password reset link is invalid or has expired.")
            return redirect('forgot_password', short_code=short_code)

    def post(self, request, short_code, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and custom_token_generator.check_token(user, token):
            password1 = request.POST.get('new_password1')
            password2 = request.POST.get('new_password2')

            if password1 and password2 and password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, "Your password has been reset successfully. You can now log in.")
                return redirect(reverse('login-page', kwargs={'short_code': short_code}))
            else:
                messages.error(request, "Passwords do not match. Please try again.")
                return render(request, self.template_name, {
                    'validlink': True,
                    'short_code': short_code,
                    'uidb64': uidb64,
                    'token': token,
                    'school': get_object_or_404(SchoolRegistration, short_code=short_code),
                })

        messages.error(request, "The password reset link is invalid or has expired.")
        return redirect('forgot_password', short_code=short_code)

    def is_token_valid(self, user, token):
        """
        Check if the token is valid and not expired.
        """
        try:
            # Extract the timestamp from the token
            ts_b36, _ = token.split("-")
            timestamp = int(ts_b36, 36)
        except ValueError:
            return False

        # Check if the token is older than 1 minute
        token_age = datetime.now() - datetime.fromtimestamp(timestamp)
        return token_age <= timedelta(minutes=1) and default_token_generator.check_token(user, token)

def forgot_password(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == "POST":
        email = request.POST.get('email')

        # Initialize user as None
        user = None

        # Check if the email belongs to the admin
        if school.admin_user and school.admin_user.email == email:
            user = school.admin_user

        # Check if the email belongs to a staff member
        if not user:
            staff_user = Staff.objects.filter(user__email=email, branches__school=school).first()
            if staff_user:
                user = staff_user.user

        # Check if the email belongs to a student
        if not user:
            student_user = Student.objects.filter(user__email=email, branch__school=school).first()
            if student_user:
                user = student_user.user

        # Check if the email belongs to a parent
        if not user:
            parent_user = ParentGuardian.objects.filter(user__email=email, school=school).first()
            if parent_user:
                user = parent_user.user

        if user:
            # Generate the token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Generate the reset link
            reset_link = request.build_absolute_uri(
                reverse(
                    'password_reset_confirm',
                    kwargs={
                        'short_code': short_code,
                        'uidb64': uid,
                        'token': token,
                    }
                )
            )

             # Send the email
            send_mail(
                subject="Password Reset Request",
                message=(
                    f"Hello {email}!\n\n"
                    "Someone has requested a link to change your password. You can do this through the link below.\n\n"
                    f"Change my password: {reset_link}\n\n"
                    "or copy and open this link in your browser:\n"
                    f"{reset_link}\n\n"
                    "If you didn't request this, please ignore this email.\n\n"
                    "Your password won't change until you access the link above and create a new one."
                ),
                from_email="noreply@AcadémiQ.com",
                recipient_list=[email],
            )


            messages.success(request, "A password reset link has been sent to your email.")
            return redirect('forgot_password', short_code=short_code)
        else:
            messages.error(request, "No account is associated with this email address in this school.")
            return redirect('forgot_password', short_code=short_code)

    context = {
        'school': school,
        'title': f'{school.school_name} Forgot Password',
    }
    return render(request, 'schools/forgot_password.html', context)

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

 # Debugging: Print out the context values
    print(f"Dashboard View Context for User {user.username}:")
    print(f"  - is_school_admin: {is_school_admin}")
    print(f"  - is_teacher: {is_teacher}")
    print(f"  - is_student: {is_student}")
    print(f"  - is_parent: {is_parent}")
    print(f"  - is_accountant: {is_accountant}")


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