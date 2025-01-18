from django.shortcuts import render, redirect, get_object_or_404
import csv
from django.core.cache import cache
from .forms import StaffCreationForm,UserUpdateForm,\
TeacherSubjectAssignmentForm,StaffUploadForm
from django.http import HttpResponse, HttpResponseBadRequest
from schools.models import SchoolRegistration, Branch 
from classes.models import TeacherSubjectClassAssignment
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage,PageNotAnInteger
from django.db.models import Q
from .models import Staff
from utils.decorator import login_required_with_short_code
from utils.permissions import admin_required,admin_or_teacher_required
from django.db import transaction
from django.http import HttpResponse
import zipfile
from io import StringIO, BytesIO
from .utils import normalize_branch_name_for_matching\
, is_valid_staff_file_name
from .tasks import process_file_task,send_staff_creation_email
import os
from django.conf import settings
from uuid import uuid4
from django.http import JsonResponse
from classes.models import Subject
from django.views.decorators.http import require_POST
from classes.forms import TeacherClassAssignmentForm
from utils.academics import get_sessions, get_terms
from academics.models import Session, Term
from utils.banking import verify_account_details,fetch_bank_codes
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse 

def save_temp_file(uploaded_file):
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_files')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)  # Ensure directory exists and is writable

    file_name = f"{uuid4().hex}_{uploaded_file.name}"
    file_path = os.path.join(temp_dir, file_name)

    with open(file_path, 'wb+') as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)

    return file_path



@login_required_with_short_code
@admin_required
@transaction.atomic
def upload_staff(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = StaffUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            # Validate the file name before proceeding
            if not is_valid_staff_file_name(uploaded_file.name, school):
                messages.error(request, "Invalid file name or format. Please download another template to fill or upload the correct one.")
                return redirect('upload_staff', short_code=short_code)

            file_path = save_temp_file(uploaded_file)

            print("Starting task to process the file")  # Debugging line
            task = process_file_task.delay(file_path, uploaded_file.name, school.id)  # Dispatch task
            print(f"Task dispatched with ID {task.id}")  # Debugging line
            
        
            messages.success(request, "File is being processed... this may take a few minutes.")
            messages.info(request, "Press ctrl + F5 on your computer if newly added names are not showing up or wait a few minutes!!!")
            return redirect('staff_list', short_code=school.short_code)
        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = StaffUploadForm()

    return render(request, 'staff/upload_staff.html', {'form': form, 'school': school})





@login_required_with_short_code
@admin_required
def download_staff_template(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)

    if not branches.exists():
        return HttpResponseBadRequest("No branches found for this school.")

    # Create an in-memory ZIP file
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:

        # Loop through each branch and generate a separate CSV file
        for branch in branches:
            # Create an in-memory CSV file for the current branch using StringIO (for text data)
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)

            # Define the headers
            headers = [
                'first_name', 'last_name', 'email', 'role', 'gender', 'marital_status',
                'date_of_birth', 'phone_number', 'address', 'nationality',
                'staff_category', 'status'
            ]
            writer.writerow(headers)

            # Add demo rows to show users how to fill the data (sample data)
            demo_data_list = [
                ['John', 'Doe', 'john.doe@example.com', 'Teacher',
                'male', 'single', '1990-01-01', '08012345678',
                '123 Demo Street', 'nigerian', 'academic', 'active'],
                ['Jane', 'Smith', 'jane.smith@example.com', 'Administrator',
                'female', 'married', '1985-05-15', '09087654321',
                '456 Example Avenue', 'non_nigerian', 'non_academic', 'active'],
                ['Michael', 'Johnson', 'michael.johnson@example.com', 'Accountant',
                'male', 'divorced', '1982-09-20', '07023456789',
                '789 Sample Road', 'nigerian', 'academic', 'inactive'],
            ]

            # Add the demo rows to the CSV
            writer.writerows(demo_data_list)

            # Normalize the branch name
            branch_name = normalize_branch_name_for_matching(branch.branch_name)

            # Determine the school type and get the correct school name and initials
            if branch.primary_school:
                # Use the primary school name and generate initials
                school_name = branch.primary_school.school_name
                school_type = "Primary"
                school_initials = ''.join([word[0].upper() for word in branch.primary_school.school_name.split()])
            elif branch.school:
                # Use the secondary school name and generate initials
                school_name = branch.school.school_name
                school_type = "Secondary"
                school_initials = ''.join([word[0].upper() for word in branch.school.school_name.split()])
            else:
                # Fallback to an unknown school name (this should rarely happen)
                school_name = "Unknown_School"
                school_type = "Unknown"
                school_initials = "UNK"

            # Generate a unique part for the file name using UUID
            unique_suffix = uuid4().hex[-3:]

            # Create the filename based on school initials, branch, and school type
            file_name = f"{school_initials}_{school_type}_{branch_name}_{unique_suffix}_staff_template.csv"

            # Move the StringIO buffer position to the start so it can be read
            csv_buffer.seek(0)

            # Convert the CSV content to bytes and write it into the ZIP file
            zip_file.writestr(file_name, csv_buffer.getvalue().encode('utf-8'))

    # Prepare the response to download the ZIP file
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response['Content-Disposition'] = f'attachment; filename={school.short_code}_staff_templates.zip'

    return response

@login_required_with_short_code
@admin_required
def pre_add_staff(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)
    return render(request, 'staff/pre_add_staff.html', {
        'school': school,

    })




@login_required_with_short_code
@admin_required
@transaction.atomic
def add_staff(request, short_code):
    # Fetch the school object and its branches
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)

    if request.method == 'POST':
        form = StaffCreationForm(request.POST, request.FILES, school=school)
        form.fields['branches'].queryset = branches

        if form.is_valid():
            # Save the user and staff object from the form
            user = form.save()

            # Generate the login URL with the short_code
            login_url = f"http://{request.get_host()}{reverse('login-page', kwargs={'short_code': short_code})}"

            # Email content
            full_name = f"{user.first_name} {user.last_name}"
            school_name = school.school_name  # Add school name dynamically
            subject = f"Welcome to {school_name} - Your Account Details"
            text_content = (
                f"Dear {full_name},\n\n"
                f"Your account has been successfully created for {school_name}.\n\n"
                f"Username: {user.username}\n"
                f"Password: 'staff' (please change it after your first login)\n\n"
                f"Log in at: {login_url}\n\n"
                f"Thank you,\nThe {school_name} Team"
            )

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; color: #343a40;">
                    <div style="max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); overflow: hidden;">
                        <!-- Header with logo -->
                        <div style="background: #007bff; color: #ffffff; padding: 20px; text-align: center;">
                            <img src="https://res.cloudinary.com/dnt2rpflv/image/upload/v1736445064/1735602377004_kiewca.png" 
                                alt="Logo" 
                                style="max-width: 100px; margin-bottom: 10px;">
                            <h4 style="margin: 0; font-size: 24px;">Welcome to {school_name}</h4>
                        </div>
                        <!-- Main content -->
                        <div style="padding: 20px;">
                            <h3 style="margin-top: 0;">Dear {full_name},</h3>
                            <p>Your account has been successfully created for <strong>{school_name}</strong>. Below are your login details:</p>
                            <p><strong>Username:</strong> {user.username}</p>
                            <p><strong>Password:</strong> 'new_staff' (please change it after your first login)</p>
                            <p style="margin: 20px 0; text-align: center;">
                                <a href="{login_url}" target="_blank" 
                                style="display: inline-block; padding: 10px 20px; background: #007bff; color: #ffffff; text-decoration: none; border-radius: 4px; font-weight: bold;">
                                    Click here to log in
                                </a>
                            </p>
                            <p>Thank you,<br>The {school_name} Team</p>
                        </div>
                        <!-- Footer -->
                        <div style="background: #f8f9fa; color: #6c757d; text-align: center; padding: 10px;">
                            <small>If you have any questions, contact us at support@school.com.</small>
                        </div>
                    </div>
                </body>
            </html>
            """


            # Send the email
            from_email = "no-reply@academiQ.com"  # Replace with your desired sender email
            to_email = [user.email]
            email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send()

            # Success message and redirect to staff list
            messages.success(
                request, f"Staff member {user.username} added successfully! An email has been sent with login details."
            )
            return redirect("staff_list", short_code=school.short_code)
        else:
            # Handle form errors and show error messages
            messages.error(request, "There was an error with your submission. Please correct the issues below.")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        # Initialize the form with the school-specific context
        form = StaffCreationForm(school=school)
        form.fields['branches'].queryset = branches

    return render(request, 'staff/add_staff.html', {
        'form': form,
        'school': school,
    })




def fetch_account_name(request):
    """
    Fetch the account name for a given account number and bank code via AJAX.
    """
    account_number = request.GET.get('account_number')
    bank_code = request.GET.get('bank_code')

    if not account_number or not bank_code:
        return JsonResponse({'error': 'Account number and bank code are required.'}, status=400)

    account_details = verify_account_details(account_number, bank_code)

    if 'account_name' in account_details:
        return JsonResponse({'account_name': account_details['account_name']})
    else:
        return JsonResponse({'error': 'Unable to verify account details.'}, status=400)

@login_required_with_short_code
@admin_required
def staff_list(request, short_code):
    # Generate a unique cache key based on the school and query parameters
    
    # Fetch the school object
    school = get_object_or_404(SchoolRegistration.objects.select_related('admin_user'), short_code=short_code)
    
    query = request.GET.get('q', '')
    per_page = request.GET.get('per_page', 10)
    status_filter = request.GET.get('status', '').lower()


    # Fetch bank codes dynamically
    bank_codes = fetch_bank_codes()
    # Use select_related and prefetch_related for optimized querying
    staff_members = Staff.objects.filter(branches__school=school).select_related('role', 'user').prefetch_related('branches').distinct()

    # Apply search query filtering
    staff_members = staff_members.filter(
        Q(user__username__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query) |
        Q(phone_number__icontains=query) |
        Q(role__name__icontains=query)
    ).distinct()

    # Apply status filtering if specified
    if status_filter in ['active', 'inactive']:
        staff_members = staff_members.filter(status=status_filter)


    # Annotate staff members with the human-readable bank name
    for staff in staff_members:
        staff.display_bank_name = bank_codes.get(staff.bank_name, "Unknown Bank")

    # Paginate the staff members list
    paginator = Paginator(staff_members, per_page)
    page = request.GET.get('page')
    
    try:
        staff_members = paginator.page(page)
    except PageNotAnInteger:
        staff_members = paginator.page(1)
    except EmptyPage:
        staff_members = paginator.page(paginator.num_pages)

    # Render the response
    response = render(request, 'staff/staff_list.html', {
        'staff_members': staff_members,
        'school': school,
        'query': query,
        'per_page': per_page,
        'status_filter': status_filter,
    })

    # Cache the rendered response for 5 minutes (300 seconds)


    return response

@login_required_with_short_code
@admin_or_teacher_required
def edit_staff(request, short_code, staff_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    staff = get_object_or_404(Staff, id=staff_id)

    branches = Branch.objects.filter(school=school)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=staff.user, school=school)
        form.fields['branches'].queryset = branches
        if form.is_valid():
            # Save the form, user and staff instance will be updated
            form.save()

            messages.success(request, 'Staff member updated successfully!')
            return redirect('schools_dashboard', short_code=school.short_code)
        else:
            messages.error(request, 'Please correct the errors below and try again.')
            # Add form errors to the messages framework
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
            
    else:
        form = UserUpdateForm(instance=staff.user, school=school)
        form.fields['branches'].queryset = branches
        form.fields['branches'].initial = staff.branches.all()

    return render(request, 'staff/edit_staff.html', {
        'form': form,
        'school': school,
        'staff': staff
    })

@login_required_with_short_code
@admin_required
def delete_staff(request, short_code, staff_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # Get the specific staff member based on ID
    staff = get_object_or_404(Staff, id=staff_id)

    # Ensure that the staff member is associated with the correct school branches
    if not staff.branches.filter(school=school).exists():
        messages.error(request, 'This staff member does not belong to this school.')
        return redirect('staff_list', short_code=school.short_code)

    if request.method == 'POST':
        user = staff.user  # Capture the associated user before deleting staff
        staff.delete()
        # Optionally, delete the user if required
        user.delete()

        messages.success(request, 'Staff member deleted successfully.')
        messages.info(request, 'press ctrl + F5 if deleted name is still showing up!!!')
        return redirect('staff_list', short_code=short_code)
    
    return render(request, 'staff/delete_staff.html', {
        'school': school,
        'staff': staff
    })

@transaction.atomic
@login_required_with_short_code
@admin_required
def assign_subjects_to_staff(request, short_code, staff_id):
    """
    Assign subjects and classes to a staff member.
    """
    # Fetch the staff and school context
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    staff = get_object_or_404(Staff, id=staff_id)
    branches = Branch.objects.filter(school=school, staff=staff).distinct()

    branch_id = request.POST.get('branch') or request.GET.get('branch')
    selected_branch = Branch.objects.get(id=branch_id) if branch_id else None

    if request.method == 'POST':
        form = TeacherSubjectAssignmentForm(request.POST, school=school, branch_id=branch_id, staff=staff)
        if form.is_valid():
            branch = form.cleaned_data['branch']
            subject = form.cleaned_data['subject']
            classes = form.cleaned_data['classes']
            session = form.cleaned_data['session']
            term = form.cleaned_data['term']

            # Unassign classes from other staff for the same subject, branch, session, and term
            existing_assignments = TeacherSubjectClassAssignment.objects.filter(
                branch=branch, subject=subject, session=session, term=term
            ).exclude(teacher=staff)

            for assignment in existing_assignments:
                # Remove conflicting classes
                conflicting_classes = assignment.classes_assigned.filter(id__in=classes.values_list('id', flat=True))
                assignment.classes_assigned.remove(*conflicting_classes)

                # If no classes are left, delete the assignment
                if assignment.classes_assigned.count() == 0:
                    assignment.delete()

            # Assign the subject to the current staff
            assignment, created = TeacherSubjectClassAssignment.objects.get_or_create(
                teacher=staff,
                subject=subject,
                branch=branch,
                session=session,
                term=term
            )
            assignment.classes_assigned.add(*classes)

            messages.success(request, f"Subject '{subject.name}' successfully assigned to {staff.user.get_full_name()} for {session.session_name}, {term.term_name}.")
            return redirect('teacher_assignments', short_code=school.short_code)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = TeacherSubjectAssignmentForm(school=school, branch_id=branch_id, staff=staff)

    return render(request, 'staff/assign_subjects.html', {
        'form': form,
        'staff': staff,
        'branches': branches,
        'selected_branch': selected_branch,
        'school': school,
    })


def get_subjects_and_classes(request, short_code, branch_id):
    # Fetch the branch using the branch_id and also ensure it belongs to the correct school using short_code
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)
    
    # Get classes and subjects for the selected branch
    classes = branch.classes.all().select_related('department')
    subjects = Subject.objects.filter(classes__in=classes).distinct()

    # Prepare the data to send as JSON response
    classes_data = [{'id': c.id, 'name': c.name, 'department': c.department.name if c.department else None} for c in classes]
    subjects_data = [{'id': s.id, 'name': s.name, 'subject_code': s.subject_code} for s in subjects]

    return JsonResponse({
        'classes': classes_data,
        'subjects': subjects_data,
    })
    
def get_classes(request, short_code, branch_id, subject_id):
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)
    subject = get_object_or_404(Subject, id=subject_id, classes__branches=branch)

    # Fetch all classes for that subject under the selected branch
    classes = subject.classes.filter(branches=branch).select_related('department').distinct()

    # Prepare the data to send as JSON response
    classes_data = [
        {
            'id': cls.id,
            'name': cls.name,
            'department': cls.department.name if cls.department else 'No Department'
        }
        for cls in classes
    ]

    return JsonResponse({'classes': classes_data})


from classes.models import Class
def get_classes_by_subject(request, short_code, branch_id, subject_id):
    """
    Fetch classes for a given subject and branch combination.
    Only classes that belong to the selected branch and are associated with the subject should be returned.
    """
    # Get the branch ensuring it belongs to the correct school by short_code
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)

    # Get the subject ensuring it is within the current school
    subject = get_object_or_404(Subject, id=subject_id)

    # Filter classes by both the branch and subject
    classes = Class.objects.filter(branches=branch, subjects=subject).select_related('department').distinct()

    # Prepare the data to send as JSON response
    classes_data = [{'id': cls.id, 'name': cls.name, 'department': cls.department.name if cls.department else None} for cls in classes]

    return JsonResponse({
        'classes': classes_data,
    })

from classes.models import TeacherClassAssignment  # Ensure you have imported the model

@login_required_with_short_code
@admin_required
def teacher_assignments_view(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    branches = Branch.objects.filter(school=school)
    sessions = Session.objects.filter(school=school)
    
    selected_branch_id = request.GET.get('branch_id')
    selected_session_id = request.GET.get('session_id')
    selected_term_id = request.GET.get('term_id')
    search_query = request.GET.get('search', '')

    selected_branch = None
    selected_session = None
    selected_term = None
    teacher_assignments = {}
    class_assignments = {}
    page_obj_subjects = None
    page_obj_classes = None

    # Subject Assignments
    if selected_branch_id:
        selected_branch = get_object_or_404(Branch, id=selected_branch_id, school=school)
        
        assignments = TeacherSubjectClassAssignment.objects.filter(branch=selected_branch)

        if selected_session_id:
            selected_session = get_object_or_404(Session, id=selected_session_id, school=school)
            assignments = assignments.filter(session=selected_session)

        if selected_term_id:
            selected_term = get_object_or_404(Term, id=selected_term_id, session=selected_session)
            assignments = assignments.filter(term=selected_term)
        
        if search_query:
            assignments = assignments.filter(
                Q(teacher__user__first_name__icontains=search_query) |
                Q(teacher__user__last_name__icontains=search_query)
            )

        # Pagination for Subject Assignments
        paginator = Paginator(assignments, 10)
        page_number = request.GET.get('page')
        page_obj_subjects = paginator.get_page(page_number)

        # Organize Subject Assignments by Teacher
        for assignment in page_obj_subjects:
            teacher = assignment.teacher
            if teacher not in teacher_assignments:
                teacher_assignments[teacher] = []
            teacher_assignments[teacher].append({
                'subject': assignment.subject,
                'classes': assignment.classes_assigned.all()
            })

    # Class Assignments
    if selected_branch_id:
        class_assignments_queryset = TeacherClassAssignment.objects.filter(branch=selected_branch)

        if selected_session_id:
            class_assignments_queryset = class_assignments_queryset.filter(session=selected_session)

        if selected_term_id:
            class_assignments_queryset = class_assignments_queryset.filter(term=selected_term)

        if search_query:
            class_assignments_queryset = class_assignments_queryset.filter(
                Q(teacher__user__first_name__icontains=search_query) |
                Q(teacher__user__last_name__icontains=search_query)
            )

        # Pagination for Class Assignments
        paginator_classes = Paginator(class_assignments_queryset, 10)
        page_number_classes = request.GET.get('page_classes')
        page_obj_classes = paginator_classes.get_page(page_number_classes)

        # Organize Class Assignments by Teacher
        for assignment in page_obj_classes:
            teacher = assignment.teacher
            if teacher not in class_assignments:
                class_assignments[teacher] = []
            class_assignments[teacher].append({
                'classes': assignment.assigned_classes.all()
            })
    print("Class Assignments:", class_assignments)
    print("Selected Branch:", selected_branch)
    print("Selected Session:", selected_session)
    print("Selected Term:", selected_term)

    return render(request, 'staff/teacher_assignments.html', {
        'school': school,
        'branches': branches,
        'sessions': sessions,
        'selected_branch': selected_branch,
        'selected_session': selected_session,
        'selected_term': selected_term,
        'teacher_assignments': teacher_assignments,
        'class_assignments': class_assignments,
        'page_obj_subjects': page_obj_subjects,
        'page_obj_classes': page_obj_classes,
        'search_query': search_query,
    })


@require_POST
@login_required_with_short_code
@admin_required
@transaction.atomic
def copy_term_assignments(request, short_code):
    """
    View to copy both subject and class assignments from one term to another term.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branch_id = request.POST.get('branch_id')
    from_session_id = request.POST.get('from_session_id')
    from_term_id = request.POST.get('from_term_id')
    to_session_id = request.POST.get('to_session_id')
    to_term_id = request.POST.get('to_term_id')

    # Ensure all required fields are filled
    if not all([branch_id, from_session_id, from_term_id, to_session_id, to_term_id]):
        messages.error(request, "Please select all the necessary fields to proceed.")
        return redirect('teacher_assignments', short_code=school.short_code)

    # Get the branch, sessions, and terms
    branch = get_object_or_404(Branch, id=branch_id, school=school)
    from_session = get_object_or_404(Session, id=from_session_id, school=school)
    from_term = get_object_or_404(Term, id=from_term_id, session=from_session)
    to_session = get_object_or_404(Session, id=to_session_id, school=school)
    to_term = get_object_or_404(Term, id=to_term_id, session=to_session)

    # Copy subject assignments
    subject_assignments = TeacherSubjectClassAssignment.objects.filter(
        branch=branch, session=from_session, term=from_term
    )
    for from_assignment in subject_assignments:
        subject_assignment, created = TeacherSubjectClassAssignment.objects.get_or_create(
            teacher=from_assignment.teacher,
            subject=from_assignment.subject,
            branch=from_assignment.branch,
            session=to_session,
            term=to_term
        )
        # Copy classes assigned to the subject
        subject_assignment.classes_assigned.set(from_assignment.classes_assigned.all())
        subject_assignment.save()

    # Copy class assignments
    class_assignments = TeacherClassAssignment.objects.filter(
        branch=branch, session=from_session, term=from_term
    )
    for from_assignment in class_assignments:
        class_assignment, created = TeacherClassAssignment.objects.get_or_create(
            teacher=from_assignment.teacher,
            branch=from_assignment.branch,
            session=to_session,
            term=to_term
        )
        # Copy classes assigned
        class_assignment.assigned_classes.set(from_assignment.assigned_classes.all())
        class_assignment.save()

    messages.success(request, "Assignments successfully copied from the selected term.")
    return redirect('teacher_assignments', short_code=school.short_code)


@require_POST
@login_required_with_short_code
@admin_required
@transaction.atomic
def copy_session_assignments(request, short_code):
    """
    View to copy both subject and class assignments from one session to another session.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branch_id = request.POST.get('branch_id')
    from_session_id = request.POST.get('from_session_id')
    to_session_id = request.POST.get('to_session_id')

    # Ensure all required fields are filled
    if not all([branch_id, from_session_id, to_session_id]):
        messages.error(request, "Please select all the necessary fields to proceed.")
        return redirect('teacher_assignments', short_code=school.short_code)

    # Get the branch, sessions
    branch = get_object_or_404(Branch, id=branch_id, school=school)
    from_session = get_object_or_404(Session, id=from_session_id, school=school)
    to_session = get_object_or_404(Session, id=to_session_id, school=school)

    # Copy subject assignments
    subject_assignments = TeacherSubjectClassAssignment.objects.filter(
        branch=branch, session=from_session
    )
    for from_assignment in subject_assignments:
        to_term = Term.objects.get(session=to_session, term_name=from_assignment.term.term_name)
        subject_assignment, created = TeacherSubjectClassAssignment.objects.get_or_create(
            teacher=from_assignment.teacher,
            subject=from_assignment.subject,
            branch=from_assignment.branch,
            session=to_session,
            term=to_term
        )
        # Copy classes assigned to the subject
        subject_assignment.classes_assigned.set(from_assignment.classes_assigned.all())
        subject_assignment.save()

    # Copy class assignments
    class_assignments = TeacherClassAssignment.objects.filter(
        branch=branch, session=from_session
    )
    for from_assignment in class_assignments:
        to_term = Term.objects.get(session=to_session, term_name=from_assignment.term.term_name)
        class_assignment, created = TeacherClassAssignment.objects.get_or_create(
            teacher=from_assignment.teacher,
            branch=from_assignment.branch,
            session=to_session,
            term=to_term
        )
        # Copy classes assigned
        class_assignment.assigned_classes.set(from_assignment.assigned_classes.all())
        class_assignment.save()

    messages.success(request, "Assignments successfully copied to the selected session.")
    return redirect('teacher_assignments', short_code=school.short_code)

@login_required_with_short_code
@admin_required
@transaction.atomic
def assign_teacher_to_class(request, short_code, teacher_id):
    # Identify the school using the short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Fetch the teacher and ensure they belong to the same school
    teacher = get_object_or_404(Staff, id=teacher_id)
    
    # Ensure the teacher belongs to branches within the school
    teacher_branches = Branch.objects.filter(school=school, staff=teacher).values_list('id', flat=True)
    
    if not teacher_branches.exists():
        messages.error(request, f"{teacher.user.first_name} {teacher.user.last_name} is not assigned to any branches under this school.")
        return redirect('teacher_assignments', short_code=short_code)

    if request.method == 'POST':
        # Debug: Print the POST data
        print("Request POST data:", request.POST)
        
        # Get the selected branch ID from the form
        branch_id = request.POST.get('branch')
        
        # Pass teacher_branches and branch_id to the form for filtering
        form = TeacherClassAssignmentForm(
            request.POST,
            teacher_branches=teacher_branches,
            branch_id=branch_id
        )
        
        if form.is_valid():
            # Retrieve session, term, branch for the assignment
            session = form.cleaned_data['session']
            term = form.cleaned_data['term']
            branch = form.cleaned_data['branch']
            assigned_classes = form.cleaned_data['assigned_classes']

            # Debug: Print cleaned data
            print(f"Class Assignments: {assigned_classes}")
            print(f"Selected Branch: {branch}")
            print(f"Selected Session: {session}")
            print(f"Selected Term: {term}")

            # Check if an assignment already exists
            assignment, created = TeacherClassAssignment.objects.get_or_create(
                teacher=teacher,
                session=session,
                term=term,
                branch=branch
            )

            # Update the assigned classes
            assignment.assigned_classes.set(assigned_classes)

            # Handle the toggle (assign_all_subjects)
            assign_all_subjects = form.cleaned_data.get('assign_all_subjects', False)
            assignment.assign_all_subjects = assign_all_subjects
            assignment.save()

            # If toggle is ON, assign all subjects in the selected classes
            if assign_all_subjects:
                for cls in assigned_classes:
                    for subject in cls.subjects.all():
                        # Create or update the subject-class assignment
                        teacher_subject_assignment, created = TeacherSubjectClassAssignment.objects.get_or_create(
                            teacher=teacher,
                            subject=subject,
                            branch=branch,
                            session=session,
                            term=term
                        )
                        # Add the class to classes_assigned
                        teacher_subject_assignment.classes_assigned.add(cls)

            # Debug: Print all assigned subjects for the teacher
            print(f"Assigned subjects for teacher {teacher.user.first_name} {teacher.user.last_name}:")
            assigned_subjects = TeacherSubjectClassAssignment.objects.filter(
                teacher=teacher,
                branch=branch,
                session=session,
                term=term
            ).select_related('subject')
            for ts in assigned_subjects:
                assigned_classes_names = [cls.name for cls in ts.classes_assigned.all()]
                print(f"Subject: {ts.subject.name}, Classes: {assigned_classes_names}")
            
            messages.success(request, f"Classes assigned to {teacher.user.first_name} successfully.")
            return redirect('teacher_assignments', short_code=short_code)
        else:
            # Debug: Print form errors if invalid

            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            print("Form errors:", form.errors)
    else:
        # Initialize the form with the teacher's branches
        form = TeacherClassAssignmentForm(teacher_branches=teacher_branches)

    context = {
        'form': form,
        'teacher': teacher,
        'school': school,
        'short_code': short_code,  
    }
    return render(request, 'staff/assign_teacher.html', context)

@login_required_with_short_code
@admin_required
def get_classes_by_branch(request, short_code, branch_id):
    # Fetch the branch ensuring it belongs to the correct school
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branch = get_object_or_404(Branch, id=branch_id, school=school)

    # Fetch classes associated with the branch
    classes = branch.classes.all().select_related('department').distinct()

    # Prepare the data to send as JSON response
    classes_data = [{'id': cls.id, 'name': cls.name, 'department': cls.department.name if cls.department else None} for cls in classes]

    return JsonResponse({'classes': classes_data})
