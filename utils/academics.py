from academics.models import Session, Term
from landingpage.models import SchoolRegistration
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from classes.models import TeacherClassAssignment, TeacherSubjectClassAssignment, Class, Subject
from schools.models import Branch
from students.models import ParentStudentRelationship

# Fetch sessions for a given school identified by the short_code
def get_sessions(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Sort sessions by ID in ascending order
    sessions = Session.objects.filter(school=school).order_by('id')

    sessions_data = [{'id': session.id, 'session_name': session.session_name} for session in sessions]
    return JsonResponse({'sessions': sessions_data})


# Fetch terms for a given session
def get_terms(request, short_code, session_id):
    session = get_object_or_404(Session, id=session_id, school__short_code=short_code)
    
    # Sort terms by ID in ascending order
    terms = Term.objects.filter(session=session).order_by('id')

    terms_data = [{'id': term.id, 'term_name': term.term_name} for term in terms]
    return JsonResponse({'terms': terms_data})


# Fetch branches for a given school
def get_branches(request, short_code):
    """
    Fetch branches for a given school, filtered by user role.
    """
    user = request.user
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher':
        # Branches assigned via class or subject assignments
        teacher = user.staff
        assigned_branches = Branch.objects.filter(
            id__in=TeacherClassAssignment.objects.filter(teacher=teacher).values_list('branch_id', flat=True)
        ) | Branch.objects.filter(
            id__in=TeacherSubjectClassAssignment.objects.filter(teacher=teacher).values_list('branch_id', flat=True)
        )
        branches = assigned_branches.distinct()
    else:
        # Admins or other authorized roles
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


def get_classes_by_branch(request, short_code, branch_id):
    """
    Fetch classes for a given branch and school, filtered by session, term, and user role.
    """
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)
    user = request.user

    # Fetch session and term from the request
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')

    # Validate session and term
    if not session_id or not term_id:
        return JsonResponse({'error': 'Session and term are required to fetch classes.'}, status=400)

    session = get_object_or_404(Session, id=session_id, school=branch.school)
    term = get_object_or_404(Term, id=term_id, session=session)

    # Check the user role
    if hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher':
        # Fetch classes assigned to the teacher for the branch, session, and term
        teacher = user.staff
        teacher_assignments = TeacherClassAssignment.objects.filter(
            teacher=teacher,
            branch=branch,
            session=session,
            term=term
        )
        classes = Class.objects.filter(
            teacher_assignments__in=teacher_assignments
        ).select_related('department').distinct().order_by('id')
    elif hasattr(user, 'parent_profile'):
        # Fetch classes related to the parent's children in the branch
        parent_relationships = ParentStudentRelationship.objects.filter(
            parent_guardian=user.parent_profile,
            student__branch=branch
        )
        classes = Class.objects.filter(
            id__in=parent_relationships.values_list('student__student_class_id', flat=True)
        ).distinct().order_by('id')
    else:
        # Fetch all classes for admins or authorized roles
        classes = Class.objects.filter(branches=branch).distinct().order_by('id')

    # Prepare data for JSON response
    classes_data = [
        {
            'id': cls.id,
            'name': cls.name,
            'department': cls.department.name if cls.department else 'No Department'
        }
        for cls in classes
    ]

    return JsonResponse({'classes': classes_data})

# Fetch subjects by branch
def get_subjects_by_branch(request, short_code, branch_id):
    """
    Fetch subjects related to a given branch, filtered by user role.
    """
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)
    user = request.user

    if hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher':
        teacher = user.staff
        # Filter subjects based on teacher assignments
        teacher_assignments = TeacherSubjectClassAssignment.objects.filter(
            teacher=teacher,
            branch=branch,
            session_id=request.GET.get('session'),
            term_id=request.GET.get('term')
        ).select_related('subject')
        subjects = Subject.objects.filter(teacher_assignments__in=teacher_assignments).distinct()
    else:
        # Admins can see all subjects in the branch
        subjects = Subject.objects.filter(classes__branches=branch).distinct()

    subjects_data = [{'id': subject.id, 'name': subject.name} for subject in subjects]
    return JsonResponse({'subjects': subjects_data})


# Fetch classes for a given subject and branch
def get_classes_by_subject(request, short_code, branch_id, subject_id):
    """
    Fetch classes for a given subject and branch, filtered by user role.
    """
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)
    subject = get_object_or_404(Subject, id=subject_id)
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')
    user = request.user

    if not session_id or not term_id:
        return JsonResponse({'error': 'Session and term are required to fetch classes.'}, status=400)

    if hasattr(user, 'staff') and user.staff.role.name.lower() == 'teacher':
        teacher = user.staff
        # Combine TeacherSubjectClassAssignment and TeacherClassAssignment filtering
        subject_class_assignments = Class.objects.filter(
            teacher_subject_classes__teacher=teacher,
            teacher_subject_classes__subject=subject,
            branches=branch,
            teacher_subject_classes__session_id=session_id,
            teacher_subject_classes__term_id=term_id
        )
        classes = (subject_class_assignments).distinct()
    else:
        # Admins can see all classes for the branch and subject
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
