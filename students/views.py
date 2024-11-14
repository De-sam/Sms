from utils.decorator import login_required_with_short_code
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


@login_required_with_short_code
@transaction.atomic
def add_parent_guardian(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Initialize form with the school context
    form = ParentGuardianCreationForm(request.POST or None, school=school)

    if request.method == 'POST' and form.is_valid():
        form.save()  # This saves both User and ParentGuardian with generated username and sends the email
        messages.success(request, 'Parent/Guardian added successfully with a login account created.')
        return redirect('parent_guardian_list', short_code=school.short_code)

    return render(request, 'parents/add_parent_guardian.html', {
        'form': form,
        'school': school,
        'branches': Branch.objects.filter(school=school),
    })


@login_required_with_short_code
@transaction.atomic
def add_student(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    form = StudentCreationForm(request.POST or None, request.FILES or None, school=school)

    if request.method == 'POST' and form.is_valid():
        # Save the student instance
        student = form.save()

        # Process each parent form
        parent_count = 0
        while f'{parent_count}-parent' in request.POST:
            parent_form = ParentAssignmentForm(request.POST, prefix=str(parent_count))

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

        # Display a success message
        messages.success(request, 'Student record has been added successfully.')
        return redirect('student_list', short_code=short_code)

    return render(request, 'students/add_student.html', {
        'form': form,
        'parent_assignment_forms': [ParentAssignmentForm(prefix='0')],  # Start with one form
        'school': school,
    })


@login_required_with_short_code
def list_parent_guardians(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Get search query from request to filter parents
    search_query = request.GET.get('search', '').strip().lower()
    all_parents = ParentGuardian.objects.all()
    
    if search_query:
        all_parents = all_parents.filter(
            first_name__icontains=search_query
        ) | all_parents.filter(
            last_name__icontains=search_query
        ) | all_parents.filter(
            phone_number__icontains=search_query
        ) | all_parents.filter(
            email__icontains=search_query
        )
    
    # Set up pagination: 10 parents per page
    paginator = Paginator(all_parents, 10)
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
@transaction.atomic
def edit_student(request, short_code, student_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    student = get_object_or_404(Student, id=student_id)
    form = StudentCreationForm(request.POST or None, request.FILES or None, instance=student, school=school)

    # Fetch current relationships for the student
    existing_relationships = ParentStudentRelationship.objects.filter(student=student)
    parent_assignment_forms = [
        ParentAssignmentForm(
            data=request.POST if request.method == 'POST' else None,
            prefix=str(i),
            initial={
                'parent': rel.parent_guardian,
                'relation_type': rel.relation_type
            }
        )
        for i, rel in enumerate(existing_relationships)
    ]

    # Add an empty form for adding new parents if not a POST request
    if request.method != 'POST':
        parent_assignment_forms.append(ParentAssignmentForm(prefix=str(len(existing_relationships))))

    if request.method == 'POST' and form.is_valid():
        # Save student details
        student = form.save()

        # Track relationships to keep
        new_relationships = []

        # Process existing forms
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
            new_parent_form = ParentAssignmentForm(request.POST, prefix=str(parent_count))
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
def student_list(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    search_query = request.GET.get('search', '').strip().lower()
    branch_filters = request.GET.getlist('branch')
    class_filters = request.GET.getlist('class')
    department_filters = request.GET.getlist('department')

    branches = Branch.objects.filter(school=school).values_list('branch_name', flat=True).distinct()
    classes = Class.objects.filter(branches__school=school).values_list('name', flat=True).distinct()
    class_objects = Class.objects.filter(branches__school=school).distinct()
    departments = Department.objects.filter(class__in=class_objects).distinct()

    all_students = Student.objects.filter(student_class__branches__school=school).distinct()
    total_students = all_students.count()
    students = all_students

    if branch_filters:
        students = students.filter(branch__branch_name__in=branch_filters)
    if class_filters:
        students = students.filter(student_class__name__in=class_filters)
    if department_filters:
        students = students.filter(student_class__department__name__in=department_filters)

    if search_query:
        students = students.filter(
            user__username__icontains=search_query
        ) | students.filter(
            first_name__icontains=search_query
        ) | students.filter(
            last_name__icontains=search_query
        )

    paginator = Paginator(students, 50)
    page = request.GET.get('page')

    try:
        students_paginated = paginator.page(page)
    except PageNotAnInteger:
        students_paginated = paginator.page(1)
    except EmptyPage:
        students_paginated = paginator.page(paginator.num_pages)

    return render(request, 'students/student_list.html', {
        'school': school,
        'branches': branches,
        'students': students_paginated,
        'departments': departments,
        'classes': classes,
        'class_objects': class_objects,
        'total_students': total_students,
        'filtered_students_count': students.count(),
        'search_query': search_query,
    })


@login_required_with_short_code
@csrf_exempt
@transaction.atomic
def bulk_delete_students(request, short_code):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_ids = data.get('student_ids', [])

            if not student_ids or any(id is None for id in student_ids):
                return JsonResponse({'success': False, 'message': 'No valid students selected.'}, status=400)

            students_to_delete = Student.objects.filter(id__in=student_ids, student_class__branches__school__short_code=short_code)

            if not students_to_delete.exists():
                return JsonResponse({'success': False, 'message': 'No valid students found for deletion.'}, status=404)

            user_ids = students_to_delete.values_list('user_id', flat=True)
            students_to_delete.delete()
            User.objects.filter(id__in=user_ids).delete()
            
            messages.success(request, 'Selected students and their associated user accounts have been deleted successfully.')
            return JsonResponse({'success': True, 'message': 'Selected students and their associated user accounts have been deleted successfully.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
    

def get_classes(request, short_code, branch_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    classes = Class.objects.filter(branches__id=branch_id, branches__school=school)
    classes_list = [{'id': cls.id, 'name': f"{cls.name} - {cls.department.name}" if cls.department else cls.name} for cls in classes]
    return JsonResponse({'classes': classes_list})
