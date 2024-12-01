from academics.models import Session, Term
from landingpage.models import SchoolRegistration
from django.http import JsonResponse
from django.shortcuts import  get_object_or_404


# Fetch sessions for a given school identified by the short_code
def get_sessions(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    sessions = Session.objects.filter(school=school)
  

    sessions_data = [{'id': session.id, 'session_name': session.session_name} for session in sessions]
    print(sessions_data)
    return JsonResponse({'sessions': sessions_data})

# Fetch terms for a given session
def get_terms(request, short_code, session_id):
    session = get_object_or_404(Session, id=session_id, school__short_code=short_code)
    terms = Term.objects.filter(session=session)


    terms_data = [{'id': term.id, 'term_name': term.term_name} for term in terms]
    print(terms_data)
    return JsonResponse({'terms': terms_data})
