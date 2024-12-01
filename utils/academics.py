from academics.models import Session, Term
from landingpage.models import SchoolRegistration
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from classes.models import Class
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
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)

    branches_data = [{'id': branch.id, 'branch_name': branch.branch_name} for branch in branches]
    return JsonResponse({'branches': branches_data})

# Fetch classes by branch for a given school
def get_classes_by_branch(request, short_code, branch_id):
    # Fetch the branch ensuring it belongs to the correct school
    branch = get_object_or_404(Branch, id=branch_id, school__short_code=short_code)

    # Fetch all classes associated with the selected branch
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

