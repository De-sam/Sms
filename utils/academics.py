from academics.models import Session, Term
from landingpage.models import SchoolRegistration
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from classes.models import TeacherClassAssignment,Class
from schools.models import Branch



# Fetch sessions for a given school identified by the short_code
def get_sessions(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    sessions = Session.objects.filter(school=school)

    sessions_data = [{'id': session.id, 'session_name': session.session_name} for session in sessions]
    return JsonResponse({'sessions': sessions_data})

# Fetch terms for a given session
def get_terms(request, short_code, session_id):
    session = get_object_or_404(Session, id=session_id, school__short_code=short_code)
    terms = Term.objects.filter(session=session)

    terms_data = [{'id': term.id, 'term_name': term.term_name} for term in terms]
    return JsonResponse({'terms': terms_data})

# Fetch branches for a given school

# Updated Function: Fetch branches for a given school with type indication
def get_branches(request, short_code):
    user = request.user
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # If user is a teacher, filter based on their assignments
    if hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher':
        teacher_assignments = TeacherClassAssignment.objects.filter(teacher=user.staff, branch__school=school)
        branches = Branch.objects.filter(teacher_class_assignments__in=teacher_assignments).distinct()
    else:
        # If the user is an admin, fetch all branches
        branches = Branch.objects.filter(school=school)

    branches_data = []
    for branch in branches:
        # Determine branch type based on whether it is linked to primary or secondary school
        if branch.primary_school:
            branch_type = 'Primary'
        elif branch.school:
            branch_type = 'Secondary'
        else:
            branch_type = 'Unknown'

        branches_data.append({
            'id': branch.id,
            'branch_name': branch.branch_name,
            'branch_type': branch_type  # Add type to indicate if it's primary or secondary
        })

    return JsonResponse({'branches': branches_data})

# Fetch classes by branch for a given school
def get_classes_by_branch(request, short_code, branch_id):
    # Fetch the branch ensuring it belongs to the correct school
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)
    user = request.user

    # Check if the user is an admin or teacher
    if hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher':
        # If the user is a teacher, only show the classes assigned to them within this branch
        teacher = user.staff
        teacher_assignments = TeacherClassAssignment.objects.filter(teacher=teacher, branch=branch)

        # Get the classes assigned to this teacher for the branch
        classes = Class.objects.filter(teacher_assignments__in=teacher_assignments).select_related('department').distinct()
    else:
        # If the user is an admin or otherwise authorized, fetch all classes in the branch
        classes = Class.objects.filter(branches=branch).select_related('department').distinct()

    # Prepare the data to send as JSON response
    classes_data = [
        {
            'id': cls.id,
            'name': cls.name,
            'department': cls.department.name if cls.department else 'No Department'
        }
        for cls in classes
    ]

    return JsonResponse({'classes': classes_data})
