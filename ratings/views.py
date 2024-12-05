from django.shortcuts import render, get_object_or_404
from academics.models import Session, Term
from schools.models import Branch
from landingpage.models import SchoolRegistration
from utils.context_helpers import get_user_roles
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from schools.models import Branch
from classes.models import Class
from students.models import Student
from .models import Rating
from django.db import transaction



def filter_students_for_ratings(request, short_code):
    """
    Render the template for filtering students based on session, term, branch, and class.
    """
    print("DEBUG: Entered filter_students_for_ratings view.")
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    user_roles = get_user_roles(request.user, school)

    context = {
        'school': school,
        'sessions': Session.objects.filter(school=school),
        'terms': Term.objects.none(),  # Dynamically populated on the frontend
        'branches': Branch.objects.filter(school=school),
        **user_roles,
    }

    print("DEBUG: Context prepared with school and user roles.")
    return render(request, 'ratings/filter_ratings.html', context)


def get_ratings(request, short_code):
    """
    Fetch filtered students based on session, term, branch, classes, and rating type.
    Includes relevant rating fields based on the selected rating type.
    """
    print("DEBUG: Entered get_ratings view.")
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            class_ids = data.get("classes", [])
            rating_type = data.get("rating_type")

            print(f"DEBUG: Filter criteria - Session: {session_id}, Term: {term_id}, Branch: {branch_id}, Classes: {class_ids}, Rating Type: {rating_type}")

            if not session_id or not term_id or not branch_id or not class_ids or not rating_type:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            session = get_object_or_404(Session, id=session_id, school=school)
            term = get_object_or_404(Term, id=term_id, session=session)
            branch = get_object_or_404(Branch, id=branch_id, school=school)

            students = Student.objects.filter(
                current_session=session,
                branch=branch,
                student_class__id__in=class_ids
            ).select_related('user')

            print(f"DEBUG: Found {students.count()} students matching criteria.")

            # Define rating fields based on rating_type
            fields = {
                        "psychomotor": ["coordination", "handwriting", "sports", "artistry", "verbal_fluency", "games", "neatness"],  # Add neatness here
                        "behavioral": ["punctuality", "attentiveness", "obedience", "leadership", "emotional_stability", "teamwork", "neatness"],  # Add neatness here
                    }.get(rating_type, [])


            student_data = []
            for student in students:
                rating = Rating.objects.filter(
                    student=student,
                    session=session,
                    term=term,
                    branch=branch,
                    rating_type=rating_type
                ).first()

                student_info = {
                    "id": student.id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                }

                for field in fields:
                    student_info[field] = getattr(rating, field, None)

                student_data.append(student_info)

            print(f"DEBUG: Prepared data for {len(student_data)} students.")
            return JsonResponse({"students": student_data, "fields": fields}, status=200)

        except json.JSONDecodeError as e:
            print(f"DEBUG: JSONDecodeError - {e}")
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            print(f"DEBUG: Exception occurred - {e}")
            return JsonResponse({"error": "An error occurred. Please try again."}, status=500)

    print("DEBUG: Invalid request method.")
    return JsonResponse({"error": "Invalid request method."}, status=405)




@csrf_exempt
def save_ratings(request, short_code):
    """
    Save ratings for students based on the submitted data.
    """
    print("DEBUG: Entered save_ratings view.")
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == "POST":
        try:
            # Parse the JSON payload
            raw_data = request.body.decode('utf-8')
            print(f"DEBUG: Raw request body: {raw_data}")
            data = json.loads(raw_data)
            print(f"DEBUG: Parsed JSON data: {data}")

            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            class_ids = data.get("classes", [])
            rating_type = data.get("rating_type")
            ratings = data.get("ratings", [])  # List of ratings per student

            print(f"DEBUG: Filter criteria - Session: {session_id}, Term: {term_id}, Branch: {branch_id}, Rating Type: {rating_type}, Ratings: {ratings}")

            # Validate required fields
            if not session_id or not term_id or not branch_id or not rating_type or not ratings:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Validate session, term, and branch
            session = get_object_or_404(Session, id=session_id, school=school)
            term = get_object_or_404(Term, id=term_id, session=session)
            branch = get_object_or_404(Branch, id=branch_id, school=school)

            # Process each rating
            with transaction.atomic():  # Ensure all records are saved or none in case of an error
                for rating_data in ratings:
                    student_id = rating_data.get("student_id")
                    if not student_id:
                        print("DEBUG: Missing student_id in ratings.")
                        continue

                    # Fetch the student
                    student = get_object_or_404(Student, id=student_id, branch=branch, current_session=session)

                    # Prepare fields for update or create
                    defaults = {}
                    if rating_type == "psychomotor":
                        defaults.update({
                            "coordination": rating_data.get("coordination") or None,
                            "handwriting": rating_data.get("handwriting") or None,
                            "sports": rating_data.get("sports") or None,
                            "artistry": rating_data.get("artistry") or None,
                            "verbal_fluency": rating_data.get("verbal_fluency") or None,
                            "games": rating_data.get("games") or None,
                        })
                    elif rating_type == "behavioral":
                        defaults.update({
                            "punctuality": rating_data.get("punctuality") or None,
                            "attentiveness": rating_data.get("attentiveness") or None,
                            "obedience": rating_data.get("obedience") or None,
                            "leadership": rating_data.get("leadership") or None,
                            "emotional_stability": rating_data.get("emotional_stability") or None,
                            "teamwork": rating_data.get("teamwork") or None,
                            "neatness": rating_data.get("neatness") or None,  # Added
                        })

                    # Save or update the rating
                    rating_obj, created = Rating.objects.update_or_create(
                        student=student,
                        session=session,
                        term=term,
                        branch=branch,
                        rating_type=rating_type,
                        defaults=defaults
                    )
                    print(f"DEBUG: {'Created' if created else 'Updated'} rating for student {student_id}. Data: {defaults}")

            print("DEBUG: Ratings saved successfully.")
            return JsonResponse({"success": True, "message": "Ratings saved successfully."}, status=200)

        except json.JSONDecodeError as e:
            print(f"DEBUG: JSONDecodeError - {e}")
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            print(f"DEBUG: Exception occurred - {e}")
            return JsonResponse({"error": "An error occurred. Please try again."}, status=500)

    print("DEBUG: Invalid request method.")
    return JsonResponse({"error": "Invalid request method."}, status=405)
