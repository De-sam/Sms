from utils.decorator import login_required_with_short_code
from utils.permissions import admin_required,admin_or_teacher_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, ParentStudentRelationship, ParentGuardian
from .forms import StudentCreationForm, ParentAssignmentForm, ParentGuardianCreationForm,ParentStudentRelationshipUpdateForm
from landingpage.models import SchoolRegistration
from schools.models import Branch
from classes.models import Class, Department
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from academics.models import Session

@login_required_with_short_code
@transaction.atomic
@admin_required
def add_parent_guardian(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    form = ParentGuardianCreationForm(request.POST or None, school=school)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Parent/Guardian added successfully.')
        return redirect('parent_guardian_list', short_code=school.short_code)

    return render(request, 'parents/add_parent_guardian.html', {
        'form': form,
        'school': school,
    })

@login_required_with_short_code
@admin_required
def edit_parent(request, short_code, parent_id):
    # Get the school and parent objects
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    parent = get_object_or_404(ParentGuardian, id=parent_id)

    # Ensure the parent belongs to the correct school
    if parent.user and not parent.user.parent_profile.school == school:
        messages.error(request, "This parent does not belong to your school.")
        return redirect('parent_guardian_list', short_code=short_code)

    # Handle form submission
    if request.method == 'POST':
        form = ParentGuardianCreationForm(request.POST, instance=parent, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, f"Parent record for {parent.first_name} {parent.last_name} has been updated successfully.")
            return redirect('parent_guardian_list', short_code=short_code)
    else:
        form = ParentGuardianCreationForm(instance=parent, school=school)

    # Render the edit parent template
    return render(request, 'parents/edit_parent.html', {
        'form': form,
        'school': school,
        'parent': parent,
    })

@login_required_with_short_code
@admin_required
@transaction.atomic
def delete_parent(request, short_code, parent_id):
    if request.method == "POST":
        # Validate the school context
        school = get_object_or_404(SchoolRegistration, short_code=short_code)
        
        # Get the parent to delete
        parent = get_object_or_404(ParentGuardian, id=parent_id, school=school)
        
        try:
            # Delete the associated user first
            if parent.user:
                parent.user.delete()
            
            # Delete the parent object
            parent.delete()

            messages.success(request, "Parent deleted successfully.")
        except Exception as e:
            messages.error(request, f"An error occurred while deleting the parent: {str(e)}")
        
        # Redirect back to the parent list
        return redirect('parent_guardian_list', short_code=short_code)
    else:
        messages.error(request, "Invalid request method.")
        return redirect('parent_guardian_list', short_code=short_code)

@login_required_with_short_code
@admin_or_teacher_required
@transaction.atomic
def add_student(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    form = StudentCreationForm(request.POST or None, request.FILES or None, school=school)

    # Initialize parent assignment forms with the school context
    parent_assignment_forms = [
        ParentAssignmentForm(prefix=str(i), school=school) for i in range(1)
    ]

    if request.method == 'POST' and form.is_valid():
        # Save the student instance
        student = form.save()

        # Process each parent form
        parent_count = 0
        while f'{parent_count}-parent' in request.POST:
            parent_form = ParentAssignmentForm(request.POST, prefix=str(parent_count), school=school)

            if parent_form.is_valid() and parent_form.cleaned_data.get('parent'):
                parent = parent_form.cleaned_data['parent']
                relation_type = parent_form.cleaned_data['relation_type']

                # Create the ParentStudentRelationship
                ParentStudentRelationship.objects.create(
                    parent_guardian=parent,
                    student=student,
                    relation_type=relation_type
                )
            parent_count += 1

        messages.success(request, 'Student record has been added successfully.')
        return redirect('student_list', short_code=short_code)

    return render(request, 'students/add_student.html', {
        'form': form,
        'parent_assignment_forms': parent_assignment_forms,
        'school': school,
    })



@login_required_with_short_code
@admin_required
def list_parent_guardians(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # List all parents linked to the school
    parents = ParentGuardian.objects.filter(school=school)

    # Apply search filter if provided
    search_query = request.GET.get('search', '').strip().lower()
    if search_query:
        parents = parents.filter(
            first_name__icontains=search_query
        ) | parents.filter(
            last_name__icontains=search_query
        ) | parents.filter(
            phone_number__icontains=search_query
        ) | parents.filter(
            email__icontains=search_query
        )

    # Paginate the results
    paginator = Paginator(parents, 10)
    page = request.GET.get('page')

    try:
        parents_paginated = paginator.page(page)
    except PageNotAnInteger:
        parents_paginated = paginator.page(1)
    except EmptyPage:
        parents_paginated = paginator.page(paginator.num_pages)

    return render(request, 'parents/list_parent_guardians.html', {
        'school': school,
        'parents': parents_paginated,
        'search_query': search_query,
    })



@login_required_with_short_code
@admin_required
@transaction.atomic
def edit_student(request, short_code, student_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    student = get_object_or_404(Student, id=student_id)

    # Initialize the main student form
    form = StudentCreationForm(request.POST or None, request.FILES or None, instance=student, school=school)

    # Fetch existing relationships for the student
    existing_relationships = ParentStudentRelationship.objects.filter(student=student)

    # Initialize parent assignment forms with school context
    parent_assignment_forms = [
        ParentAssignmentForm(
            data=request.POST if request.method == 'POST' else None,
            prefix=str(i),
            initial={
                'parent': rel.parent_guardian,
                'relation_type': rel.relation_type
            },
            school=school  # Pass the school context
        )
        for i, rel in enumerate(existing_relationships)
    ]

    # Add an empty form for adding new parents
    if request.method != 'POST':
        parent_assignment_forms.append(ParentAssignmentForm(prefix=str(len(existing_relationships)), school=school))

    if request.method == 'POST' and form.is_valid():
        # Save student details
        student = form.save()

        # Track relationships to keep
        new_relationships = []

        # Process each parent form
        for i, parent_form in enumerate(parent_assignment_forms):
            delete_field = request.POST.get(f'delete-{i}', 'false')
            if delete_field == 'true':
                # If marked for deletion, delete the relationship
                relationship_to_delete = existing_relationships[i]
                relationship_to_delete.delete()
                continue

            if parent_form.is_valid() and parent_form.cleaned_data.get('parent'):
                parent = parent_form.cleaned_data['parent']
                relation_type = parent_form.cleaned_data['relation_type']

                # Update or create the relationship
                relationship, created = ParentStudentRelationship.objects.get_or_create(
                    student=student,
                    parent_guardian=parent,
                    defaults={'relation_type': relation_type}
                )
                if not created and relationship.relation_type != relation_type:
                    relationship.relation_type = relation_type
                    relationship.save()

                new_relationships.append(relationship.id)

        # Handle any additional parent forms added dynamically
        parent_count = len(existing_relationships)
        while f'{parent_count}-parent' in request.POST:
            new_parent_form = ParentAssignmentForm(request.POST, prefix=str(parent_count), school=school)
            if new_parent_form.is_valid() and new_parent_form.cleaned_data.get('parent'):
                parent = new_parent_form.cleaned_data['parent']
                relation_type = new_parent_form.cleaned_data['relation_type']

                relationship = ParentStudentRelationship.objects.create(
                    student=student,
                    parent_guardian=parent,
                    relation_type=relation_type
                )
                new_relationships.append(relationship.id)
            parent_count += 1

        # Delete any relationships that were not retained
        existing_relationships.exclude(id__in=new_relationships).delete()

        messages.success(request, 'Student record has been updated successfully.')
        return redirect('student_list', short_code=short_code)

    return render(request, 'students/edit_students.html', {
        'form': form,
        'parent_assignment_forms': parent_assignment_forms,
        'school': school,
        'student': student,
    })



@login_required_with_short_code
@admin_required
def student_list(request, short_code):
    # Get the school based on the short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # Get all sessions for the school
    sessions = Session.objects.filter(school=school)

    # Determine the session filter
    selected_session_id = request.GET.get('session')
    print('selected session id is:',selected_session_id)
    if selected_session_id:
        try:
            selected_session = sessions.get(id=selected_session_id)
        except Session.DoesNotExist:
            selected_session = sessions.filter(is_active=True).first()
    else:
        # Use the current session as the default
        selected_session = sessions.filter(is_active=True).first()

    # Filter students based on the selected session and the school's branches
    students = Student.objects.filter(branch__school=school, current_session=selected_session).distinct()

    # Apply search and additional filters
    search_query = request.GET.get('search', '').strip().lower()
    branch_filters = request.GET.getlist('branch')
    class_filters = request.GET.getlist('class')
    department_filters = request.GET.getlist('department')

    if search_query:
        students = students.filter(
            first_name__icontains=search_query
        ) | students.filter(
            last_name__icontains=search_query
        ) | students.filter(
            user__username__icontains=search_query
        )

    if branch_filters:
        print(f"Filtering by branches: {branch_filters}")  # Debugging log
        students = students.filter(branch__branch_name__in=branch_filters)
    if class_filters:
        print(f"Filtering by classes: {class_filters}")  # Debugging log
        students = students.filter(student_class__name__in=class_filters)
    if department_filters:
        print(f"Filtering by departments: {department_filters}")  # Debugging log
        students = students.filter(student_class__department__name__in=department_filters)
    # Pagination
    paginator = Paginator(students, 10)
    page = request.GET.get('page')

    try:
        students_paginated = paginator.page(page)
    except PageNotAnInteger:
        students_paginated = paginator.page(1)
    except EmptyPage:
        students_paginated = paginator.page(paginator.num_pages)

    # Get filter options
    branches = Branch.objects.filter(school=school).values_list('branch_name', flat=True).distinct()
    classes = Class.objects.filter(branches__school=school).values_list('name', flat=True).distinct()
    class_objects = Class.objects.filter(branches__school=school).distinct()
    departments = Department.objects.filter(class__in=class_objects).distinct()

    return render(request, 'students/student_list.html', {
        'school': school,
        'sessions': sessions,
        'selected_session': selected_session,
        'branches': branches,
        'students': students_paginated,
        'departments': departments,
        'classes': classes,
        'class_objects': class_objects,
        'total_students': students.count(),
        'search_query': search_query,
    })


@csrf_protect
@transaction.atomic
def bulk_delete_students(request, short_code):
    """
    Deletes selected students and their associated user accounts.
    """
    if request.method == 'POST':
        try:
            # Parse request data
            data = json.loads(request.body)
            student_ids = data.get('student_ids', [])

            if not student_ids:
                return JsonResponse({'success': False, 'message': 'No students selected for deletion.'}, status=400)

            # Validate the school
            school = get_object_or_404(SchoolRegistration, short_code=short_code)

            # Fetch students to delete
            students_to_delete = Student.objects.filter(
                id__in=student_ids,
                student_class__branches__school=school
            ).distinct()

            if not students_to_delete.exists():
                return JsonResponse({'success': False, 'message': 'No valid students found for deletion.'}, status=404)

            # Collect associated user IDs
            user_ids = students_to_delete.values_list('user_id', flat=True)

            # Delete users first to ensure cascading relationships
            User.objects.filter(id__in=user_ids).delete()

            # Explicitly delete students to ensure related signals or custom logic is applied
            for student in students_to_delete:
                student.delete()

            messages.success(request, 'Student record has been deleted successfully.')
            return JsonResponse({'success': True, 'message': 'Selected students and their associated user accounts have been deleted successfully.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data provided.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method. Only POST requests are allowed.'}, status=405)
    

def get_classes(request, short_code, branch_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    classes = Class.objects.filter(branches__id=branch_id, branches__school=school)
    classes_list = [{'id': cls.id, 'name': f"{cls.name} - {cls.department.name}" if cls.department else cls.name} for cls in classes]
    return JsonResponse({'classes': classes_list})
