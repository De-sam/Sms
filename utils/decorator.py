from functools import wraps
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from landingpage.models import SchoolRegistration
from schools.models import Branch
from students.models import Student, ParentStudentRelationship

def login_required_with_short_code(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        short_code = kwargs.get('short_code', 'default')

        # Check if user is authenticated
        if not request.user.is_authenticated:
            login_url = reverse('login-page', kwargs={'short_code': short_code})
            return redirect(f'{login_url}?next={request.path}')

        # Get the school based on the short_code
        school = get_object_or_404(SchoolRegistration, short_code=short_code)

        # Check if the user is the admin user
        if request.user == school.admin_user:
            return view_func(request, *args, **kwargs)

        # Check if the user is a staff member and belongs to the school
        if hasattr(request.user, 'staff') and request.user.staff.branches.filter(school=school).exists():
            return view_func(request, *args, **kwargs)

        # Check if the user is a student and belongs to a branch of the school
        if hasattr(request.user, 'student_profile') and request.user.student_profile.branch.school == school:
            return view_func(request, *args, **kwargs)

        # Check if the user is a parent and has children in the school
        if hasattr(request.user, 'parent_guardian'):
            # Check if any of the parent's children are in the school
            if ParentStudentRelationship.objects.filter(
                parent_guardian=request.user.parent_guardian,
                student__branch__school=school
            ).exists():
                return view_func(request, *args, **kwargs)

        # If no valid authorization, redirect with error
        messages.error(request, 'You are not authorized to access this school.')
        login_url = reverse('login-page', kwargs={'short_code': short_code})
        return redirect(f'{login_url}?next={request.path}')

    return _wrapped_view
