from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from academics.models import Session, Term
from schools.models import Branch
from classes.models import Class
from students.models import Student
from landingpage.models import SchoolRegistration
from utils.context_helpers import get_user_roles
from .models import Comment
import json

def filter_students_for_comments(request, short_code):
    """
    Render the template for filtering students based on session, term, branch, and class.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    user_roles = get_user_roles(request.user, school)

    context = {
        'school': school,
        'sessions': Session.objects.filter(school=school),
        'terms': Term.objects.none(),  # Dynamically populated on the frontend
        'branches': Branch.objects.filter(school=school),
        **user_roles,
    }
    return render(request, 'comments/filter_comments.html', context)


@csrf_exempt
def get_comments(request, short_code):
    """
    Fetch filtered students based on session, term, branch, and classes, including their comments.
    """
    print("DEBUG: Entered get_comments view.")
    
    # Ensure the school is valid
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    print(f"DEBUG: School found - {school}")

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            class_ids = data.get("classes", [])
            
            print(f"DEBUG: Received Data - Session: {session_id}, Term: {term_id}, Branch: {branch_id}, Classes: {class_ids}")

            # Validate input fields
            if not session_id or not term_id or not branch_id or not class_ids:
                print("DEBUG: Missing required fields.")
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Get related objects
            session = get_object_or_404(Session, id=session_id, school=school)
            term = get_object_or_404(Term, id=term_id, session=session)
            branch = get_object_or_404(Branch, id=branch_id, school=school)
            print(f"DEBUG: Validated session, term, branch.")

            # Fetch students and their comments
            students = Student.objects.filter(
                current_session=session,
                branch=branch,
                student_class__id__in=class_ids
            ).select_related('user')
            print(f"DEBUG: Found {students.count()} students matching criteria.")

            student_data = []
            for student in students:
                # Fetch comment for each student
                comment = Comment.objects.filter(
                    student=student,
                    session=session,
                    term=term
                ).first()

                student_data.append({
                    "id": student.id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "comment_text": comment.comment_text if comment else ""
                })

            print(f"DEBUG: Prepared data for {len(student_data)} students.")
            return JsonResponse({"students": student_data}, status=200)

        except json.JSONDecodeError as e:
            print(f"DEBUG: JSONDecodeError - {e}")
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            print(f"DEBUG: Exception occurred - {e}")
            return JsonResponse({"error": "An error occurred. Please try again."}, status=500)

    print("DEBUG: Invalid request method.")
    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
@transaction.atomic
def save_comments(request, short_code):
    """
    Save comments for students based on the submitted data.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            session_id = data.get("session")
            term_id = data.get("term")
            comments = data.get("comments", [])

            # Validate required fields
            if not session_id or not term_id or not comments:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Fetch related objects
            session = get_object_or_404(Session, id=session_id, school=school)
            term = get_object_or_404(Term, id=term_id, session=session)

            # Process each comment
            for comment_data in comments:
                student_id = comment_data.get("student_id")
                comment_text = comment_data.get("comment_text")

                if not student_id or not comment_text:
                    continue  # Skip incomplete entries

                student = get_object_or_404(Student, id=student_id, current_session=session)

                # Create or update the comment
                Comment.objects.update_or_create(
                    student=student,
                    session=session,
                    term=term,
                    author=request.user,
                    defaults={'comment_text': comment_text}
                )

            return JsonResponse({"success": True, "message": "Comments saved successfully."})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)
