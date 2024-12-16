from academics.models import Session, Term
from landingpage.models import SchoolRegistration
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from classes.models import TeacherClassAssignment, TeacherSubjectClassAssignment, Class, Subject
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
        direct_class_assignments = Class.objects.filter(
            teacher_assignments__teacher=teacher,
            branches=branch
        )
        classes = (subject_class_assignments | direct_class_assignments).distinct()
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
