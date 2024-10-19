from utils.decorator import login_required_with_short_code
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from .models import Student, ParentStudentRelationship
from .forms import StudentCreationForm, ParentStudentRelationshipForm, ParentGuardianCreationForm
from landingpage.models import SchoolRegistration
from schools.models import Branch
from classes.models import Class,Department

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
def student_list(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Fetch branches as list of strings (branch names)
    branches = Branch.objects.filter(school=school).values_list('branch_name', flat=True).distinct()
    
    # Fetch classes as list of strings (class names)
    classes = Class.objects.filter(branches__school=school).values_list('name', flat=True).distinct()
    
    # Fetch actual Class model instances
    class1 = Class.objects.filter(branches__school=school).distinct()
    
    # Use the Class model instances to query Departments
    departments = Department.objects.filter(class__in=class1).distinct()
    
    # Fetch students related to the school
    students = Student.objects.filter(student_class__branches__school=school).select_related('user', 'student_class', 'branch')

    # Debugging output
    print(f'classes (names): {classes}')
    print(f'class1 (instances): {class1}')
    print(f'departments: {departments}')

    return render(request, 'students/student_list.html', {
        'school': school,
        'branches': branches,
        'students': students,
        'departments': departments,  
        'classes': classes,  # Pass class names
        'class_objects': class1,  # Pass actual class objects if needed in the template
    })

def get_classes(request, short_code, branch_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    classes = Class.objects.filter(branches__id=branch_id, branches__school=school)
    classes_list = [{'id': cls.id, 'name': f"{cls.name} - {cls.department.name}" if cls.department else cls.name} for cls in classes]
    return JsonResponse({'classes': classes_list})
