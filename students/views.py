# students/views.py
from utils.decorator import login_required_with_short_code
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, ParentStudentRelationship
from .forms import StudentCreationForm, ParentStudentRelationshipForm, ParentGuardianCreationForm
from landingpage.models import SchoolRegistration
from schools.models import Branch
from classes.models import Class
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse


@login_required_with_short_code
@transaction.atomic
def add_parent_guardian(request, short_code):
    # Fetch the school object using the short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Fetch the branches linked to the school
    branches = Branch.objects.filter(school=school)

    if request.method == 'POST':
        form = ParentGuardianCreationForm(request.POST)
        if form.is_valid():
            parent_guardian = form.save(commit=False)
            parent_guardian.save()

            messages.success(request, 'Parent/Guardian added successfully!')
            return redirect('parent_guardian_list', short_code=school.short_code)  # Adjust redirect URL as needed
    else:
        form = ParentGuardianCreationForm()

    return render(request, 'parents/add_parent_guardian.html', {
        'form': form,
        'school': school,
        'branches': branches  # If you need branches for the form or for future extension
    })

@login_required_with_short_code
def add_student(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = StudentCreationForm(request.POST, request.FILES, school=school)
        parent_student_relationship_form = ParentStudentRelationshipForm(request.POST)
        
        if form.is_valid() and parent_student_relationship_form.is_valid():
            try:
                student = form.save()
                parent_student_relationship = parent_student_relationship_form.save(commit=False)
                parent_student_relationship.student = student
                parent_student_relationship.save()
                
                messages.success(request, "Student added successfully!")
                return redirect('student_list', short_code=short_code)
            except Exception as e:
                print(f"Error saving form: {e}")
        else:
            print("Form is invalid")
            print(form.errors)
            print(parent_student_relationship_form.errors)
    else:
        form = StudentCreationForm(school=school)
        parent_student_relationship_form = ParentStudentRelationshipForm()

    context = {
        'form': form,
        'parent_student_relationship_form': parent_student_relationship_form,
        'school': school,
    }
    return render(request, 'students/add_student.html', context)

@login_required_with_short_code
def student_list(request, short_code):
    # Fetch the school based on the short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # Fetch the branches associated with this school and get unique branch names
    branches = Branch.objects.filter(school=school).values_list('branch_name', flat=True).distinct()

    # Fetch the classes associated with these branches and get unique class names
    classes = Class.objects.filter(branches__school=school).values_list('name', flat=True).distinct()

    # Fetch the students in these classes and that belong to the specific school
    students = Student.objects.filter(student_class__branches__school=school).select_related('user', 'student_class', 'branch')

    context = {
        'school': school,
        'branches': branches,
        'students': students,
        'classes': classes
    }

    return render(request, 'students/student_list.html', context)

def get_classes(request, short_code, branch_id):
    # Fetch the school using the short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # Fetch the classes for the given branch, ensuring that the branch is linked to the specified school
    classes = Class.objects.filter(branches__id=branch_id, branches__school=school)

    # Create a list of classes with their department names included
    classes_list = [
        {
            'id': cls.id,
            'name': f"{cls.name} - {cls.department.name}" if cls.department else cls.name
        } for cls in classes
    ]

    return JsonResponse({'classes': classes_list})