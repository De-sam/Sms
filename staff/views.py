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
from django.db import transaction
from django.http import HttpResponse
import zipfile
from io import StringIO, BytesIO
from .utils import normalize_branch_name_for_matching\
, is_valid_staff_file_name
from .tasks import process_file_task
import os
from django.conf import settings
from uuid import uuid4

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
            
            # Instead of redirecting, render the page with the task ID to be used by JavaScript
            messages.success(request, "File is being processed... this may take a few minutes.")
            messages.info(request, "Press ctrl + F5 on your computer if newly added names are not showing up or wait a few minutes!!!")
            return redirect('staff_list', short_code=school.short_code)
        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = StaffUploadForm()

    return render(request, 'staff/upload_staff.html', {'form': form, 'school': school})





@login_required_with_short_code
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
def add_staff(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)
    
    if request.method == 'POST':
        form = StaffCreationForm(request.POST, request.FILES, school=school)
        form.fields['branches'].queryset = branches
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            staff = Staff.objects.create(
                user=user,
                role=form.cleaned_data['role'],
                gender=form.cleaned_data['gender'],
                marital_status=form.cleaned_data['marital_status'],
                date_of_birth=form.cleaned_data['date_of_birth'],
                phone_number=form.cleaned_data['phone_number'],
                address=form.cleaned_data['address'],
                nationality=form.cleaned_data['nationality'],
                staff_category=form.cleaned_data['staff_category'],
                status=form.cleaned_data['status'],
                cv=form.cleaned_data.get('cv'),
                profile_picture=form.cleaned_data.get('profile_picture'),
                staff_signature=form.cleaned_data.get('staff_signature'),
            )

            staff.branches.set(form.cleaned_data['branches'])
            staff.save()

            messages.success(request, 'Staff member added successfully!')
            return redirect('staff_list', short_code=school.short_code)
        else:
            messages.error(request, 'Please correct the errors below and try again.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = StaffCreationForm(school=school)
        form.fields['branches'].queryset = branches

    return render(request, 'staff/add_staff.html', {
        'form': form,
        'school': school,

    })


@login_required_with_short_code
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

            
            # Optimize this part by fetching the data once
            existing_assignments = TeacherSubjectClassAssignment.objects.filter(
                subject=subject,
                branch=branch,
                classes_assigned__in=classes
            ).exclude(teacher=staff).prefetch_related('classes_assigned')

            # Unassign the subject from the selected classes for any other teacher in the same branch
            for assignment in existing_assignments:
                assignment.classes_assigned.remove(*classes)
                if assignment.classes_assigned.count() == 0:
                    assignment.delete()

            # Create or update the assignment for the current teacher in the specific branch
            assignment, created = TeacherSubjectClassAssignment.objects.get_or_create(
                teacher=staff,
                subject=subject,
                branch=branch
            )
            assignment.classes_assigned.add(*classes)
            assignment.save()

            messages.success(request, f'Subjects and classes assigned to {staff.user.first_name} successfully!')
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


@login_required_with_short_code
def teacher_assignments_view(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    branches = Branch.objects.filter(school=school)
    
    selected_branch_id = request.GET.get('branch_id')
    search_query = request.GET.get('search', '')

    selected_branch = None
    teacher_assignments = {}
    page_obj = None  # Initialize page_obj as None

    if selected_branch_id:
        selected_branch = get_object_or_404(Branch, id=selected_branch_id, school=school)
        assignments = TeacherSubjectClassAssignment.objects.filter(branch=selected_branch).select_related('teacher', 'subject').prefetch_related('classes_assigned')
        
        if search_query:
            assignments = assignments.filter(teacher__user__first_name__icontains=search_query) | assignments.filter(teacher__user__last_name__icontains=search_query)
        
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
        'selected_branch': selected_branch,
        'teacher_assignments': teacher_assignments,
        'page_obj': page_obj,
        'search_query': search_query
    })