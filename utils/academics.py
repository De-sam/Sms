from academics.models import Session, Term
from landingpage.models import SchoolRegistration
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from classes.models import TeacherClassAssignment,Class
from schools.models import Branch
from classes.models import Class, Subject
from classes.models import TeacherClassAssignment,TeacherSubjectClassAssignment


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
    """
    Fetch branches for a given school, filtered by user role.
    """
    user = request.user
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher':
        # Fetch branches explicitly assigned to the teacher
        teacher = user.staff
        teacher_assignments = TeacherClassAssignment.objects.filter(
            teacher=teacher, branch__school=school
        ).values_list('branch', flat=True).distinct()
        branches = Branch.objects.filter(id__in=teacher_assignments)
    else:
        # For admins or other authorized roles, fetch all branches for the school
        branches = Branch.objects.filter(school=school)

    # Prepare branch data with types
    branches_data = [
        {
            'id': branch.id,
            'branch_name': branch.branch_name,
            'branch_type': 'Primary' if branch.primary_school else 'Secondary' if branch.school else 'Unknown'
        }
        for branch in branches
    ]

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



def get_subjects_by_branch(request, short_code, branch_id):
    """
    Fetch subjects related to a given branch, with role-based filtering.
    """
    # Fetch the branch, ensuring it belongs to the correct school using short_code
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)
    user = request.user

    if hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher':
        # Filter subjects based on the teacher's assignments for the selected branch
        teacher = user.staff
        teacher_assignments = TeacherSubjectClassAssignment.objects.filter(
            teacher=teacher,
            branch=branch,
            session_id=request.GET.get('session'),  # Ensure session is passed as a query parameter
            term_id=request.GET.get('term')  # Ensure term is passed as a query parameter
        ).select_related('subject')
        
        # Collect the assigned subjects
        subjects = Subject.objects.filter(
            teacher_assignments__in=teacher_assignments
        ).distinct()
    else:
        # For admins, fetch all subjects related to classes in the branch
        subjects = Subject.objects.filter(
            classes__branches=branch
        ).distinct()

    # Prepare the response data
    subjects_data = [{'id': subject.id, 'name': subject.name} for subject in subjects]
    return JsonResponse({'subjects': subjects_data})

def get_classes_by_subject(request, short_code, branch_id, subject_id):
    """
    Fetch classes for a given subject and branch combination, with role-based filtering.
    """
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)
    subject = get_object_or_404(Subject, id=subject_id)
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')
    user = request.user

    if not session_id or not term_id:
        return JsonResponse({'error': 'Session and term are required to fetch classes.'}, status=400)

    if hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher':
        # Fetch classes assigned to the teacher for this subject and branch
        teacher = user.staff
        teacher_assignments = TeacherSubjectClassAssignment.objects.filter(
            teacher=teacher,
            branch=branch,
            subject=subject,
            session_id=session_id,
            term_id=term_id
        )
        classes = Class.objects.filter(
            teacher_subject_classes__in=teacher_assignments
        ).select_related('department').distinct()
    else:
        # Fetch all classes for the branch and subject for admins
        classes = Class.objects.filter(
            branches=branch,
            subjects=subject
        ).select_related('department').distinct()

    classes_data = [
        {
            'id': cls.id,
            'name': cls.name,
            'department': cls.department.name if cls.department else 'No Department'
        }
        for cls in classes
    ]

    return JsonResponse({'classes': classes_data})