from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import StaffCreationForm,UserUpdateForm,TeacherSubjectAssignmentForm
from schools.models import SchoolRegistration, Branch
from classes.models import TeacherSubjectClassAssignment,Subject
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Staff
from utils.decorator import login_required_with_short_code


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
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    query = request.GET.get('q', '')
    per_page = request.GET.get('per_page', 10)
    status_filter = request.GET.get('status', '').lower()

    staff_members = Staff.objects.filter(branches__school=school).distinct()

    staff_members = staff_members.filter(
    Q(user__username__icontains=query) |
    Q(user__first_name__icontains=query) |
    Q(user__last_name__icontains=query) |
    Q(user__email__icontains=query) |
    Q(phone_number__icontains=query) |
    Q(role__name__icontains=query)
).distinct()

    if status_filter in ['active', 'inactive']:
        staff_members = staff_members.filter(status=status_filter)

    paginator = Paginator(staff_members, per_page)
    page = request.GET.get('page')
    try:
        staff_members = paginator.page(page)
    except PageNotAnInteger:
        staff_members = paginator.page(1)
    except EmptyPage:
        staff_members = paginator.page(paginator.num_pages)

    return render(request, 'staff/staff_list.html', {
        'staff_members': staff_members,
        'school': school,
        'query': query,
        'per_page': per_page,
        'status_filter': status_filter,
    })

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
        return redirect('staff_list', short_code=short_code)

    if request.method == 'POST':
        user = staff.user  # Capture the associated user before deleting staff
        staff.delete()
        # Optionally, delete the user if required
        user.delete()

        messages.success(request, 'Staff member deleted successfully.')
        return redirect('staff_list', short_code=short_code)
    
    return render(request, 'staff/delete_staff.html', {
        'school': school,
        'staff': staff
    })

@login_required_with_short_code
def assign_subjects_to_staff(request, short_code, staff_id):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    print(f"School: {school}")

    staff = get_object_or_404(Staff, id=staff_id)
    print(f"Staff: {staff}")

    branches = Branch.objects.filter(school=school, staff__id=staff.id).distinct()
    print(f"Filtered Branches for Staff: {branches}")

    branch_id = request.POST.get('branch')
    print(f"Selected Branch ID (POST): {branch_id}")

    if not branch_id:
        branch_id = request.GET.get('branch')
        print(f"Selected Branch ID (GET): {branch_id}")

    selected_branch = None

    if branch_id:
        selected_branch = Branch.objects.get(id=branch_id)
        print(f"Selected Branch: {selected_branch}")

    if request.method == 'POST':
        form = TeacherSubjectAssignmentForm(request.POST, school=school, branch_id=branch_id, staff=staff)
        if form.is_valid():
            branch = form.cleaned_data['branch']
            subject = form.cleaned_data['subject']
            classes = form.cleaned_data['classes']
            print(f"Form Valid: Branch: {branch}, Subject: {subject}, Classes: {classes}")

            assignment, created = TeacherSubjectClassAssignment.objects.get_or_create(teacher=staff, subject=subject)
            assignment.classes_assigned.set(classes)
            assignment.save()

            messages.success(request, f'Subjects and classes assigned to {staff.user.first_name} successfully!')
            return redirect('staff_list', short_code=school.short_code)
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