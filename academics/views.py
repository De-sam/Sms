from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Session, Term
from .forms import SessionForm, TermForm
from landingpage.models import SchoolRegistration
from utils.decorator import login_required_with_short_code  # Assuming you have this decorator defined
from utils.permissions import admin_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# View to Create a New Session for the Current School using short_code
@login_required_with_short_code
@admin_required
def create_session(request, short_code):
    # Get the school associated with the provided short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.school = school  # Associate the session with the current school
            session.save()
            messages.success(request, 'New session created successfully!')
            return redirect('list_sessions', short_code=short_code)  # Redirect to a session list view
    else:
        form = SessionForm()

    return render(request, 'academics/create_session.html', {'form': form, 'school': school})

@login_required_with_short_code
@admin_required
def list_sessions(request, short_code):
    # Get the school associated with the provided short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # Get all sessions for the current school
    sessions = Session.objects.filter(school=school).order_by('-start_date')

    # Pagination for sessions (10 per page)
    paginator = Paginator(sessions, 10)
    page = request.GET.get('page')

    try:
        sessions_paginated = paginator.page(page)
    except PageNotAnInteger:
        sessions_paginated = paginator.page(1)
    except EmptyPage:
        sessions_paginated = paginator.page(paginator.num_pages)

    return render(request, 'academics/list_sessions.html', {
        'school': school,
        'sessions': sessions_paginated,
    })

# View to Edit an Existing Session using short_code
@login_required_with_short_code
@admin_required
def edit_session(request, short_code, pk):
    # Get the school associated with the provided short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    session = get_object_or_404(Session, pk=pk, school=school)

    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Session updated successfully!')
            return redirect('list_sessions', short_code=short_code)
    else:
        form = SessionForm(instance=session)

    return render(request, 'academics/edit_session.html', {'form': form, 'session': session, 'school': school})

# View to Add a New Term for a Specific Session of the Current School using short_code
@login_required_with_short_code
@admin_required
def add_term(request, short_code, session_id):
    # Get the school associated with the provided short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    session = get_object_or_404(Session, id=session_id, school=school)

    if request.method == 'POST':
        form = TermForm(request.POST)
        if form.is_valid():
            term = form.save(commit=False)
            term.session = session  # Link the term to the session
            term.save()
            messages.success(request, 'New term added successfully!')
            return redirect('list_terms', short_code=short_code)  # Redirect to a term list view
    else:
        form = TermForm(initial={'session': session})

    return render(request, 'academics/add_term.html', {'form': form, 'session': session, 'school': school})

@login_required_with_short_code
@admin_required
def list_terms(request, short_code, session_id):
    # Get the school associated with the provided short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    # Get the specific session for which terms are to be listed
    session = get_object_or_404(Session, id=session_id, school=school)

    # Get all terms for the current session
    terms = Term.objects.filter(session=session).order_by('term_name')

    # Pagination for terms (10 per page)
    paginator = Paginator(terms, 10)
    page = request.GET.get('page')

    try:
        terms_paginated = paginator.page(page)
    except PageNotAnInteger:
        terms_paginated = paginator.page(1)
    except EmptyPage:
        terms_paginated = paginator.page(paginator.num_pages)

    return render(request, 'academics/list_terms.html', {
        'school': school,
        'session': session,
        'terms': terms_paginated,
    })

# View to Edit an Existing Term using short_code
@login_required_with_short_code
@admin_required
def edit_term(request, short_code, pk):
    # Get the school associated with the provided short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # Get the specific term associated with the provided pk and ensure it belongs to the correct session under the current school
    term = get_object_or_404(Term, pk=pk, session__school=school)

    if request.method == 'POST':
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            messages.success(request, 'Term updated successfully!')
            # Redirect to list_terms and pass the session_id from the term object
            return redirect('list_terms', short_code=short_code, session_id=term.session.id)  # Update this line
    else:
        form = TermForm(instance=term)

    return render(request, 'academics/edit_term.html', {'form': form, 'term': term, 'school': school})
