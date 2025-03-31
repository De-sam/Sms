from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from ratings.models import RatingCriteria
from schools.models import Branch
from landingpage.models import SchoolRegistration
from utils.decorator import login_required_with_short_code
from utils.permissions import admin_or_teacher_required,admin_required
from academics.models import Session, Term
from django.http import JsonResponse
from students.models import Student
from ratings.models import Rating, RatingCriteria
from django.views.decorators.csrf import csrf_exempt
import json




@login_required_with_short_code
@admin_required
def manage_rating_criteria(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)
    selected_branch_ids = request.GET.getlist('branches')
    selected_rating_type = request.GET.get('rating_type')
    criteria = []

    if request.method == 'POST':
        selected_branch_ids = request.POST.getlist('branches')
        selected_rating_type = request.POST.get('rating_type')
        criteria_names = request.POST.getlist('criteria_name')
        max_values = request.POST.getlist('max_value')

        # Save criteria for selected branches
        for branch_id in selected_branch_ids:
            branch = get_object_or_404(Branch, id=branch_id, school=school)
            for name, max_value in zip(criteria_names, max_values):
                if name and max_value:
                    RatingCriteria.objects.update_or_create(
                        school=school,
                        branch=branch,
                        rating_type=selected_rating_type,
                        criteria_name=name,
                        defaults={'max_value': max_value},
                    )

        messages.success(request, "Rating criteria updated successfully!")
        return redirect('manage_rating_criteria', short_code=short_code)

    # Fetch existing criteria if branches and rating type are selected
    if selected_branch_ids and selected_rating_type:
        criteria = RatingCriteria.objects.filter(
            branch_id__in=selected_branch_ids, 
            rating_type=selected_rating_type
        )

    return render(request, 'ratings/manage_rating_criteria.html', {
        'school': school,
        'branches': branches,
        'selected_branch_ids': [int(b) for b in selected_branch_ids],
        'selected_rating_type': selected_rating_type,
        'criteria': criteria,
    })



@login_required_with_short_code
@admin_or_teacher_required
def manage_ratings(request, short_code):
    """
    View for managing student ratings with filtering options.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    return render(request, 'ratings/manage_ratings.html', {
        'school': school,
    })


@csrf_exempt
@login_required_with_short_code
@admin_or_teacher_required
def fetch_students_and_criteria(request, short_code):
    """
    API to fetch students, rating criteria, and existing scores based on filters.
    """
    branch_id = request.GET.get('branch')
    class_id = request.GET.get('class')
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')
    rating_type = request.GET.get('rating_type')

    # Ensure all required filters are provided
    if not all([branch_id, class_id, session_id, term_id, rating_type]):
        return JsonResponse({'error': 'All filters are required.'}, status=400)

    try:
        # Validate school
        school = get_object_or_404(SchoolRegistration, short_code=short_code)

        # Get related objects
        session = get_object_or_404(Session, id=session_id, school=school)
        term = get_object_or_404(Term, id=term_id, session=session)
        branch = get_object_or_404(Branch, id=branch_id, school=school)

        # Fetch students filtered by session, term, branch, and class
        students = Student.objects.filter(
            current_session=session,
            branch=branch,
            student_class_id=class_id
        ).select_related('student_class').order_by('last_name')

        # Fetch rating criteria
        criteria = RatingCriteria.objects.filter(
            branch=branch,
            rating_type=rating_type
        )

        # Fetch existing ratings for the filtered students and criteria
        ratings = Rating.objects.filter(
            session=session,
            term=term,
            branch=branch,
            criteria__in=criteria,
            student__in=students  # Ensure ratings belong to the filtered students
        )

        # Prepare student data
        student_data = [
            {'id': student.id, 'name': f"{student.last_name} {student.first_name}"}
            for student in students
        ]

        # Prepare criteria data
        criteria_data = [
            {'id': criterion.id, 'name': criterion.criteria_name, 'max_value': criterion.max_value}
            for criterion in criteria
        ]

        # Prepare existing ratings data
        rating_data = [
            {'student_id': rating.student.id, 'criterion_id': rating.criteria.id, 'value': rating.value}
            for rating in ratings
        ]

        return JsonResponse({
            'students': student_data,
            'criteria': criteria_data,
            'ratings': rating_data
        })

    except Exception as e:
        # Handle errors gracefully
        return JsonResponse({"error": str(e)}, status=500)

@login_required_with_short_code
@admin_or_teacher_required
@csrf_exempt
def save_ratings(request, short_code):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            rating_type = data.get("rating_type")
            ratings_data = data.get("ratings", [])

            if not all([session_id, term_id, branch_id, rating_type, ratings_data]):
                return JsonResponse({"error": "Missing required fields."}, status=400)

            for rating in ratings_data:
                student_id = rating.get("student_id")
                criterion_id = rating.get("criterion_id")
                value = rating.get("value")

                if not all([student_id, criterion_id, value]):
                    continue  # Skip invalid ratings

                try:
                    student = Student.objects.get(id=student_id)
                    criteria = RatingCriteria.objects.get(id=criterion_id)

                    # Save or update the rating
                    Rating.objects.update_or_create(
                        student=student,
                        session_id=session_id,
                        term_id=term_id,
                        branch_id=branch_id,
                        criteria=criteria,
                        defaults={"value": value, "rating_type": rating_type},
                    )
                except RatingCriteria.DoesNotExist:
                    return JsonResponse({"error": f"Invalid criterion ID: {criterion_id}"}, status=400)
                except Student.DoesNotExist:
                    return JsonResponse({"error": f"Invalid student ID: {student_id}"}, status=400)

            return JsonResponse({"success": "Ratings saved successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=400)
