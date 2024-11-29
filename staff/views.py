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
from utils.permissions import admin_required
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

            # Send the account creation email asynchronously
            send_staff_creation_email.delay(user.email, user.username, school.short_code)

            # Success message and redirect to staff list
            messages.success(request, f'Staff member {user.username} added successfully! An email has been sent with login details.')
            return redirect('staff_list', short_code=school.short_code)
        else:
            # Handle form errors and show error messages
            messages.error(request, 'There was an error with your submission. Please correct the issues below.')
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

@login_required_with_short_code
@admin_required
def staff_list(request, short_code):
    # Generate a unique cache key based on the school and query parameters
    cache_key = f"staff_list_{short_code}_{request.GET.get('q', '')}_{request.GET.get('page', 1)}_{request.GET.get('status', '').lower()}"
    cached_staff_list = cache.get(cache_key)

    # Check if the result is already cached
    if cached_staff_list:
        return cached_staff_list

    # Fetch the school object
    school = get_object_or_404(SchoolRegistration.objects.select_related('admin_user'), short_code=short_code)
    
    query = request.GET.get('q', '')
    per_page = request.GET.get('per_page', 10)
    status_filter = request.GET.get('status', '').lower()

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
    cache.set(cache_key, response, 300)

    return response

@login_required_with_short_code
@admin_required
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
            return redirect('staff_list', short_code=school.short_code)
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
@admin_required
@login_required_with_short_code
def assign_subjects_to_staff(request, short_code, staff_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    staff = get_object_or_404(Staff, id=staff_id)
    branches = Branch.objects.filter(school=school, staff__id=staff.id).distinct()

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

            # Create or update the assignment for the current teacher, subject, branch, session, and term
            assignment, created = TeacherSubjectClassAssignment.objects.get_or_create(
                teacher=staff,
                subject=subject,
                branch=branch,
                session=session,
                term=term
            )
            assignment.classes_assigned.add(*classes)
            assignment.save()

            messages.success(request, f'Subjects and classes assigned to {staff.user.first_name} successfully for {session.session_name}, {term.term_name}!')
            return redirect('teacher_assignments', short_code=school.short_code)
        else:
            print(f"Form Errors: {form.errors}")
    else:
        form = TeacherSubjectAssignmentForm(school=school, branch_id=branch_id, staff=staff)

    return render(request, 'staff/assign_subjects.html', {
        'form': form,
        'school': school,
        'staff': staff,
        'branches': branches,
        'selected_branch': selected_branch,
    })

from academics.models import Session, Term
# Fetch sessions for a given school identified by the short_code
def get_sessions(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    sessions = Session.objects.filter(school=school)
  

    sessions_data = [{'id': session.id, 'session_name': session.session_name} for session in sessions]
    print(sessions_data)
    return JsonResponse({'sessions': sessions_data})

# Fetch terms for a given session
def get_terms(request, short_code, session_id):
    session = get_object_or_404(Session, id=session_id, school__short_code=short_code)
    terms = Term.objects.filter(session=session)


    terms_data = [{'id': term.id, 'term_name': term.term_name} for term in terms]
    print(terms_data)
    return JsonResponse({'terms': terms_data})

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
    # Fetch the branch and ensure it belongs to the correct school
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)
    
    # Fetch the subject and ensure it belongs to the correct branch
    subject = get_object_or_404(Subject, id=subject_id, classes__branches=branch)

    # Fetch all classes for that subject under the selected branch
    classes = subject.classes.filter(branches=branch).distinct()

    # Prepare the data to send as JSON response
    classes_data = [{'id': c.id, 'name': c.name} for c in classes]

    return JsonResponse({
        'classes': classes_data,
    })

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
    page_obj = None  # Initialize page_obj as None

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

        # Pagination
        paginator = Paginator(assignments, 10)  # Show 10 assignments per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Organize assignments by teacher
        for assignment in page_obj:
            teacher = assignment.teacher
            if teacher not in teacher_assignments:
                teacher_assignments[teacher] = []
            teacher_assignments[teacher].append({
                'subject': assignment.subject,
                'classes': assignment.classes_assigned.all()
            })

    return render(request, 'staff/teacher_assignments.html', {
        'school': school,
        'branches': branches,
        'sessions': sessions,
        'selected_branch': selected_branch,
        'selected_session': selected_session,
        'selected_term': selected_term,
        'teacher_assignments': teacher_assignments,
        'page_obj': page_obj,
        'search_query': search_query,
    })


@require_POST
@login_required_with_short_code
@admin_required
@transaction.atomic
def copy_term_assignments(request, short_code):
    """
    View to copy teacher assignments from one term to another term.
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

    # Fetch all assignments from the source term
    assignments = TeacherSubjectClassAssignment.objects.filter(branch=branch, session=from_session, term=from_term)

    # Assuming `to_term_assignments` is the queryset of assignments for the "To Term"
    for from_assignment in assignments:
        assignment, created = TeacherSubjectClassAssignment.objects.get_or_create(
            teacher=from_assignment.teacher,
            subject=from_assignment.subject,
            branch=from_assignment.branch,
            session=to_session,
            term=to_term,
    )
    
    # Instead of direct assignment, use `.set()` method
    assignment.classes_assigned.set(from_assignment.classes_assigned.all())
    assignment.save()

    messages.success(request, "Assignments successfully copied from the selected term.")
    return redirect('teacher_assignments', short_code=school.short_code)


@require_POST
@login_required_with_short_code
@admin_required
@transaction.atomic
def copy_session_assignments(request, short_code):
    """
    View to copy all assignments from one session to another session.
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

    # Fetch all assignments from the source session (all terms)
    assignments = TeacherSubjectClassAssignment.objects.filter(branch=branch, session=from_session)

    # Copy each assignment to the target session, for all terms
    for assignment in assignments:
        to_term = Term.objects.get(session=to_session, term_name=assignment.term.term_name)  # Match the term name
        
        # Create or get the assignment without setting the many-to-many field
        new_assignment, created = TeacherSubjectClassAssignment.objects.get_or_create(
            teacher=assignment.teacher,
            subject=assignment.subject,
            branch=assignment.branch,
            session=to_session,
            term=to_term
        )

        # Use `.set()` to copy the classes assigned
        new_assignment.classes_assigned.set(assignment.classes_assigned.all())
        new_assignment.save()

    messages.success(request, "Assignments successfully copied to the selected session.")
    return redirect('teacher_assignments', short_code=school.short_code)

