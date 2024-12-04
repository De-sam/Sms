from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from academics.models import Session, Term
from schools.models import Branch
from students.models import Student
from .forms import RatingFilterForm, RatingForm
from .models import Rating
from django.db import transaction

@transaction.atomic
def filter_students_for_ratings(request, short_code):
    # Get the school
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    # Initialize variables
    students = []
    selected_classes = []
    rating_type = None

    if request.method == 'POST':
        # Process the filter form
        filter_form = RatingFilterForm(request.POST, school=school)
        
        if filter_form.is_valid():
            # Get the cleaned data from the form
            session = filter_form.cleaned_data['session']
            term = filter_form.cleaned_data['term']
            rating_type = filter_form.cleaned_data['rating_type']
            branch = filter_form.cleaned_data['branch']
            selected_classes = filter_form.cleaned_data['classes']

            # Fetch students in the selected classes
            students = Student.objects.filter(
                student_class__in=selected_classes,
                current_session=session,
                branch=branch
            ).distinct()

            if not students.exists():
                messages.warning(request, "No students found for the selected criteria.")

    else:
        # Initialize an empty form
        filter_form = RatingFilterForm(school=school)

    # Generate rating forms dynamically for the filtered students
    rating_forms = []
    for student in students:
        # Fetch an existing rating record if it exists
        rating = Rating.objects.filter(
            student=student,
            session=session,
            term=term,
            branch=branch,
            rating_type=rating_type
        ).first()

        # Initialize a rating form
        form = RatingForm(instance=rating, rating_type=rating_type)
        form.fields['student'].initial = student
        rating_forms.append(form)

    # Render the template
    return render(request, 'ratings/filter_ratings.html', {
        'filter_form': filter_form,
        'students': students,
        'rating_forms': rating_forms,
        'rating_type': rating_type,
        'school': school,
    })
