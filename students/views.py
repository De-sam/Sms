from utils.decorator import login_required_with_short_code
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student
from .forms import StudentCreationForm, ParentStudentRelationshipForm,\
    ParentGuardianCreationForm, StudentUpdateForm
from landingpage.models import SchoolRegistration
from schools.models import Branch
from classes.models import Class,Department
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json

@login_required_with_short_code
@transaction.atomic
def add_parent_guardian(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    form = ParentGuardianCreationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Parent/Guardian added successfully!')
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
    parent_student_relationship_form = ParentStudentRelationshipForm(request.POST or None)

    if request.method == 'POST' and form.is_valid() and parent_student_relationship_form.is_valid():
        student = form.save()  # Now this returns a Student instance
        parent_student_relationship = parent_student_relationship_form.save(commit=False)
        parent_student_relationship.student = student  # Correctly assign the Student instance here
        parent_student_relationship.save()
        messages.success(request, "Student added successfully!")
        return redirect('student_list', short_code=short_code)

    return render(request, 'students/add_student.html', {
        'form': form,
        'parent_student_relationship_form': parent_student_relationship_form,
        'school': school,
    })


@login_required_with_short_code
@transaction.atomic
def edit_student(request, short_code, student_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    student = get_object_or_404(Student, id=student_id, branch__school=school)

    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, request.FILES, instance=student, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('student_list', short_code=short_code)
    else:
        # Prepopulate the email field with the related User's email
        initial_data = {
            'email': student.user.email,
        }
        form = StudentUpdateForm(instance=student, school=school, initial=initial_data)

    return render(request, 'students/edit_students.html', {
        'form': form,
        'school': school,
        'student': student,
    })



@login_required_with_short_code
def student_list(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # Get search query and filters from request
    search_query = request.GET.get('search', '').strip().lower()
    branch_filters = request.GET.getlist('branch')
    class_filters = request.GET.getlist('class')
    department_filters = request.GET.getlist('department')

    # Fetch branches, classes, and departments for filtering options
    branches = Branch.objects.filter(school=school).values_list('branch_name', flat=True).distinct()
    classes = Class.objects.filter(branches__school=school).values_list('name', flat=True).distinct()
    class_objects = Class.objects.filter(branches__school=school).distinct()
    departments = Department.objects.filter(class__in=class_objects).distinct()

    # Fetch all students related to the school (before any filtering)
    all_students = Student.objects.filter(
        student_class__branches__school=school
    ).distinct()
    total_students = all_students.count()  # Total number of students in the database

    # Apply search and filters to get the filtered student list
    students = all_students

    # Apply branch filter if any branch is selected
    if branch_filters:
        students = students.filter(branch__branch_name__in=branch_filters)

    # Apply class filter if any class is selected
    if class_filters:
        students = students.filter(student_class__name__in=class_filters)

    # Apply department filter if any department is selected
    if department_filters:
        students = students.filter(student_class__department__name__in=department_filters)

    # Apply search query filter
    if search_query:
        students = students.filter(
            user__username__icontains=search_query
        ) | students.filter(
            first_name__icontains=search_query
        ) | students.filter(
            last_name__icontains=search_query
        )

    # Set up pagination: 10 students per page
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
        'total_students': total_students,  # Pass total students count
        'filtered_students_count': students.count(),  # Pass filtered students count
        'search_query': search_query,
    })


from django.contrib import messages

@login_required_with_short_code
@csrf_exempt
@transaction.atomic
def bulk_delete_students(request, short_code):
    print(f"Request method: {request.method}")
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_ids = data.get('student_ids', [])
            print(f"Received student IDs for deletion: {student_ids}")

            if not student_ids or any(id is None for id in student_ids):
                return JsonResponse({'success': False, 'message': 'No valid students selected.'}, status=400)

            students_to_delete = Student.objects.filter(
                id__in=student_ids, 
                student_class__branches__school__short_code=short_code
            )

            if not students_to_delete.exists():
                return JsonResponse({'success': False, 'message': 'No valid students found for deletion.'}, status=404)

            # Perform the deletion
            students_to_delete.delete()
            
            # Set a success message to be displayed on the next page load
            messages.success(request, 'Selected students have been deleted successfully.')
            
            return JsonResponse({'success': True, 'message': 'Selected students have been deleted successfully.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    else:
        print("Invalid request method received.")
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

    

def get_classes(request, short_code, branch_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    classes = Class.objects.filter(branches__id=branch_id, branches__school=school)
    classes_list = [{'id': cls.id, 'name': f"{cls.name} - {cls.department.name}" if cls.department else cls.name} for cls in classes]
    return JsonResponse({'classes': classes_list})
