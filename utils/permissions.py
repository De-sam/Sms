from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from landingpage.models import SchoolRegistration
from students.models import ParentStudentRelationship


def admin_required(view_func):
    """Decorator to check if the user is an admin."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        school = get_object_or_404(SchoolRegistration, short_code=kwargs.get('short_code'))
        if request.user != school.admin_user:
            raise PermissionDenied("You do not have permission to access this view.")
        return view_func(request, *args, **kwargs)
    return wrapper

def teacher_required(view_func):
    """Decorator to check if the user is a teacher."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'staff') and request.user.staff.role.name.lower() == 'teacher':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("You do not have permission to access this view.")
    return wrapper

def student_required(view_func):
    """Decorator to check if the user is a student."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        school = get_object_or_404(SchoolRegistration, short_code=kwargs.get('short_code'))
        if hasattr(request.user, 'student_profile') and request.user.student_profile.branch.school == school:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("You do not have permission to access this view.")
    return wrapper

def accountant_required(view_func):
    """Decorator to check if the user is an accountant."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'staff') and request.user.staff.role.name.lower() == 'accountant':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("You do not have permission to access this view.")
    return wrapper

def accountant_or_admin_required(view_func):
    """Decorator to check if the user is an accountant."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        school = get_object_or_404(SchoolRegistration, short_code=kwargs.get('short_code'))
        if hasattr(request.user, 'staff') and request.user.staff.role.name.lower() == 'accountant':
            return view_func(request, *args, **kwargs)
        # Check if user is admin
        if request.user == school.admin_user:
            return view_func(request, *args, **kwargs)

        raise PermissionDenied("You do not have permission to access this view.")
    return wrapper


def parent_required(view_func):
    """Decorator to check if the user is a parent."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        school = get_object_or_404(SchoolRegistration, short_code=kwargs.get('short_code'))
        if hasattr(request.user, 'parent_profile'):
            # Check if the parent has any students in the given school
            if ParentStudentRelationship.objects.filter(
                parent_guardian=request.user.parent_profile,
                student__branch__school=school
            ).exists():
                return view_func(request, *args, **kwargs)
        raise PermissionDenied("You do not have permission to access this view.")
    return wrapper

def parent_or_admin_required(view_func):
    """Decorator to check if the user is a parent."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        school = get_object_or_404(SchoolRegistration, short_code=kwargs.get('short_code'))
        if hasattr(request.user, 'parent_profile'):
            # Check if the parent has any students in the given school
            if ParentStudentRelationship.objects.filter(
                parent_guardian=request.user.parent_profile,
                student__branch__school=school
            ).exists():
                return view_func(request, *args, **kwargs)
            # Check if user is admin
        if request.user == school.admin_user:
                return view_func(request, *args, **kwargs)

        raise PermissionDenied("You do not have permission to access this view.")
    return wrapper


def admin_or_teacher_required(view_func):
    """Decorator to check if the user is either an admin or a teacher."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        school = get_object_or_404(SchoolRegistration, short_code=kwargs.get('short_code'))
        
        # Check if user is admin
        if request.user == school.admin_user:
            return view_func(request, *args, **kwargs)

        # Check if user is a teacher
        if hasattr(request.user, 'staff') and request.user.staff.role.name.lower() == 'teacher':
            return view_func(request, *args, **kwargs)
        
        # If neither, raise PermissionDenied
        raise PermissionDenied("You do not have permission to access this view.")
    
    return wrapper

def student_admin_required(view_func):
    """Decorator to check if the user is a student admin."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        school = get_object_or_404(SchoolRegistration, short_code=kwargs.get('short_code'))

        # Check if user is admin
        if request.user == school.admin_user:
            return view_func(request, *args, **kwargs)
        
        # If not a student admin
        if hasattr(request.user, 'student_profile') and request.user.student_profile.branch.school == school:
            return view_func(request, *args, **kwargs)
        
        raise PermissionDenied("You do not have permission to access this view.")
    
    return wrapper

def admin_student_parent_required(view_func):
    """
    Decorator to check if the user is either:
    - School admin
    - Student belonging to the school
    - Parent of a student in the school
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        school = get_object_or_404(SchoolRegistration, short_code=kwargs.get('short_code'))
        
        # Check if user is admin
        if request.user == school.admin_user:
            return view_func(request, *args, **kwargs)
        
        # Check if user is a student in this school
        if hasattr(request.user, 'student_profile') and request.user.student_profile.branch.school == school:
            return view_func(request, *args, **kwargs)
        
        # Check if user is a parent with children in this school
        if hasattr(request.user, 'parent_profile'):
            if ParentStudentRelationship.objects.filter(
                parent_guardian=request.user.parent_profile,
                student__branch__school=school
            ).exists():
                return view_func(request, *args, **kwargs)
        
        raise PermissionDenied("You do not have permission to access this view.")
    
    return wrapper

