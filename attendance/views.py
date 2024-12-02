from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction, IntegrityError
from academics.models import Session, Term
from schools.models import Branch
from landingpage.models import SchoolRegistration
from classes.models import Class
from .models import SchoolDaysOpen, StudentAttendance
from .forms import SchoolDaysOpenForm, StudentAttendanceFilterForm, StudentAttendanceForm
from students.models import Student
from utils.decorator import login_required_with_short_code
from utils.permissions import admin_required
from django.http import JsonResponse

@login_required_with_short_code
@admin_required
@transaction.atomic
def set_school_days_open(request, short_code):
    # Get the school and its branches
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)

    if request.method == 'POST':
        form = SchoolDaysOpenForm(request.POST)
        form.fields['branches'].queryset = branches  # Ensure branches are unique to the current school

        if form.is_valid():
            # Extract cleaned data
            session = form.cleaned_data['session']
            term = form.cleaned_data['term']
            branches = form.cleaned_data['branches']
            days_open = form.cleaned_data['days_open']
            
            try:
                # Loop through each selected branch and create/update SchoolDaysOpen records
                for branch in branches:
                    school_days_open, created = SchoolDaysOpen.objects.update_or_create(
                        branch=branch,
                        session=session,
                        term=term,
                        defaults={'days_open': days_open}
                    )

                # Success message after setting school days open successfully
                messages.success(request, f'School days open set successfully for {session.session_name}, {term.term_name}!')
                return redirect('set_school_days_open', short_code=short_code)

            except IntegrityError:
                # Handle duplicate entry attempts by displaying an error message
                messages.error(request, f'An entry for {session.session_name}, {term.term_name} already exists for one of the selected branches. Please update the existing entry instead.')
    
    else:
        # Initialize an empty form and limit branches to the current school
        form = SchoolDaysOpenForm()
        form.fields['branches'].queryset = branches

    # Render the template for setting school days open
    return render(request, 'attendance/set_school_days_open.html', {
        'form': form,
        'school': school,
    })


@login_required_with_short_code
@admin_required
@transaction.atomic
def record_student_attendance(request, short_code):
    # Get the school and branches related to the school
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)

    students = []  # Initialize empty list for students
    days_open = None

    if request.method == 'POST':
        filter_form = StudentAttendanceFilterForm(request.POST, school=school)

        if filter_form.is_valid():
            # Extract form data
            session = filter_form.cleaned_data['session']
            term = filter_form.cleaned_data['term']
            branch = filter_form.cleaned_data['branch']
            selected_classes = filter_form.cleaned_data['classes']

            # Get number of days school opened
            try:
                days_open = SchoolDaysOpen.objects.get(branch=branch, session=session, term=term).days_open
            except SchoolDaysOpen.DoesNotExist:
                messages.error(request, 'Number of days school opened is not set for the selected branch, session, and term.')
                return render(request, 'attendance/record_student_attendance.html', {
                    'filter_form': filter_form,
                    'students': [],
                    'days_open': None,
                    'attendance_forms': [],
                    'school': school,
                })

            # Fetch students who are in the selected classes, linked to the correct session and branch
            students = Student.objects.filter(
                student_class__in=selected_classes,
                current_session=session,
                branch=branch
            ).distinct()

            if not students.exists():
                messages.warning(request, "No students found for the selected filter criteria.")

    else:
        filter_form = StudentAttendanceFilterForm(school=school)

    # Create attendance forms for students found
    attendance_forms = []
    for student in students:
        # Fetch existing attendance record for each student
        attendance_record = StudentAttendance.objects.filter(
            session=session,
            term=term,
            branch=branch,
            student_class=student.student_class,
            student=student,
        ).first()
        
        form = StudentAttendanceForm(instance=attendance_record)
        form.fields['student'].initial = student
        attendance_forms.append(form)

    context = {
        'filter_form': filter_form,
        'students': students,
        'days_open': days_open,  # Add days_open to the context to display in the template
        'attendance_forms': attendance_forms,
        'school': school,
    }

    return render(request, 'attendance/student_attendance.html', context)


def get_attendance(request, short_code):
    # Ensure the school context is correctly fetched
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    print(f"School: {school}")

    # Extract parameters from request
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')
    branch_id = request.GET.get('branch')
    class_ids = request.GET.get('classes', '').split(',')

    # Fetch session, term, and branch ensuring they belong to the correct school
    session = get_object_or_404(Session, id=session_id, school=school)
    term = get_object_or_404(Term, id=term_id, session=session)
    branch = get_object_or_404(Branch, id=branch_id, school=school)

    # Fetch number of days school opened
    try:
        days_open = SchoolDaysOpen.objects.get(branch=branch, session=session, term=term).days_open
    except SchoolDaysOpen.DoesNotExist:
        days_open = None  # No record of days school opened for selected branch, session, and term

    # Fetch selected classes under the given branch
    selected_classes = Class.objects.filter(id__in=class_ids, branches=branch)

    # Get attendance records for students in the selected classes
    student_attendance_records = []
    for selected_class in selected_classes:
        students = Student.objects.filter(
            student_class=selected_class,
            current_session=session,
            branch=branch
        )

        for student in students:
            attendance_record = StudentAttendance.objects.filter(
                student=student,
                session=session,
                term=term,
                student_class=selected_class
            ).first()

            student_data = {
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'attendance_count': attendance_record.attendance_count if attendance_record else 0
            }
            student_attendance_records.append(student_data)

    # Print the final collected attendance data
    print(f"Student Attendance Records: {student_attendance_records}")

    # Return data as JSON response to the frontend, including the number of days school opened
    return JsonResponse({
        'students': student_attendance_records,
        'days_open': days_open,  # Include number of days school was open
    })


@login_required_with_short_code
@admin_required
@transaction.atomic
def save_student_attendance(request, short_code):
    # Handling attendance data submission
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        # Debugging: Print the incoming POST data
        print(f"POST data received: {request.POST}")

        # Extract data from the POST request
        session_id = request.POST.get('session')
        term_id = request.POST.get('term')
        branch_id = request.POST.get('branch')

        # Debugging: Print extracted session, term, and branch IDs
        print(f"Session ID: {session_id}, Term ID: {term_id}, Branch ID: {branch_id}")

        # Fetch session, term, and branch objects
        session = get_object_or_404(Session, id=session_id, school=school)
        term = get_object_or_404(Term, id=term_id, session=session)
        branch = get_object_or_404(Branch, id=branch_id, school=school)

        # Extract attendance data from the POST request
        student_ids = []
        attendance_counts = []

        for key in request.POST.keys():
            if key.startswith('attendance_'):
                try:
                    student_id = int(key.split('_')[1])  # Extract student ID
                    attendance_count = int(request.POST[key])  # Get attendance count
                    student_ids.append(student_id)
                    attendance_counts.append(attendance_count)
                except ValueError as e:
                    print(f"Error parsing data for key {key}: {e}")

        if len(student_ids) != len(attendance_counts):
            print("Error: Mismatch between student IDs and attendance counts.")
            return JsonResponse({'success': False, 'message': "Mismatch between students and attendance counts."}, status=400)

        # Save attendance records
        for student_id, attendance_count in zip(student_ids, attendance_counts):
            try:
                student = get_object_or_404(Student, id=student_id)

                # Retrieve the student's class
                student_class = student.student_class  # Assuming `student_class` is correctly set on the `Student` model

                if not student_class:
                    print(f"Student {student_id} does not have an assigned class.")
                    return JsonResponse({'success': False, 'message': f"Student {student.full_name()} does not have a class."}, status=400)

                # Create or update the attendance record
                attendance_record, created = StudentAttendance.objects.update_or_create(
                    student=student,
                    session=session,
                    term=term,
                    branch=branch,
                    student_class=student_class,  # Set the student's class
                    defaults={'attendance_count': attendance_count}
                )

                if created:
                    print(f"Created attendance record for student {student_id}.")
                else:
                    print(f"Updated attendance record for student {student_id}.")

            except Exception as e:
                print(f"Failed to save attendance for student {student_id}: {e}")
                return JsonResponse({'success': False, 'message': f"Failed to save attendance for student {student_id}."}, status=400)

        # Success response
        print("All attendance records have been updated successfully.")
        return JsonResponse({'success': True, 'message': "Attendance records updated successfully."})

    # Return error for non-POST requests
    return JsonResponse({'success': False, 'message': "Invalid request method."}, status=405)
