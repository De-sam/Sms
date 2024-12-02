# utils/context_helpers.py
from students.models import ParentStudentRelationship

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
