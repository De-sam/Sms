# utils/context_helpers.py
from students.models import ParentStudentRelationship
from landingpage.models import SchoolRegistration


def get_user_roles(user, school):
    """Utility function to determine user roles."""
    is_school_admin = user == school.admin_user
    is_teacher = hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher'
    is_student = hasattr(user, 'student_profile') and user.student_profile.branch.school == school
    is_parent = hasattr(user, 'parent_profile') and ParentStudentRelationship.objects.filter(
        parent_guardian=user.parent_profile,
        student__branch__school=school
    ).exists()
    is_accountant = hasattr(user, 'staff') and user.staff.role.name.lower() == 'accountant'

    return {
        'is_school_admin': is_school_admin,
        'is_teacher': is_teacher,
        'is_student': is_student,
        'is_parent': is_parent,
        'is_accountant': is_accountant,
    }
def user_roles_context(request):
    """Context processor to add user roles and related objects to templates."""
    if not request.user.is_authenticated:
        return {}

    context = {
        'is_school_admin': False,
        'is_teacher': False,
        'is_student': False,
        'is_parent': False,
        'is_accountant': False,
        'student': None,
        'staff': None,
        'parent': None,
    }

    # Attempt to fetch the school based on the short_code in the URL
    short_code = request.resolver_match.kwargs.get('short_code', None) if request.resolver_match else None
    school = None
    if short_code:
        try:
            school = SchoolRegistration.objects.get(short_code=short_code)
        except SchoolRegistration.DoesNotExist:
            pass

    # Populate roles if school is found
    if school:
        roles = get_user_roles(request.user, school)
        context.update(roles)

        # Add role-specific objects
        if roles['is_student']:
            context['student'] = request.user.student_profile
        if roles['is_teacher'] or roles['is_accountant']:
            context['staff'] = request.user.staff
        if roles['is_parent']:
            context['parent'] = request.user.parent_profile

    return context
