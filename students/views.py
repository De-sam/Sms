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

def add_student(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = StudentCreationForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Student added successfully!")
                return redirect('student_list', short_code=short_code)
            except Exception as e:
                print(f"Error saving form: {e}")
        else:
            print("Form is invalid")
            print(form.errors)  
    else:
        form = StudentCreationForm(school=school)

    context = {
        'form': form,
        'school': school,
    }
    return render(request, 'students/add_student.html', context)

@login_required_with_short_code
def student_list(request, short_code):
    # Fetch the school based on the short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # Fetch the branches associated with this school
    branches = Branch.objects.filter(school=school)

    # Fetch the classes associated with these branches
    classes = Class.objects.filter(branches__in=branches)

    # Fetch the students in these classes
    students = Student.objects.filter(student_class__in=classes).select_related('user', 'student_class', 'branch')

    context = {
        'school': school,
        'branches': branches,
        'students': students
    }

    return render(request, 'students/student_list.html', context)

def get_classes(request, branch_id):
    classes = Class.objects.filter(branch__id=branch_id)
    classes_list = [{'id': cls.id, 'name': cls.name} for cls in classes]
    return JsonResponse({'classes': classes_list})