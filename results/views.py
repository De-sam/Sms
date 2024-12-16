from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.forms import modelformset_factory
from django.core.paginator import Paginator
from .models import ResultStructure, ResultComponent
from .forms import ResultStructureForm, ResultComponentForm
from landingpage.models import SchoolRegistration
from utils.decorator import login_required_with_short_code
from utils.permissions import admin_required,admin_or_teacher_required
from utils.context_helpers import get_user_roles
from classes.models import Subject
from django.http import QueryDict
from .forms import ScoreFilterForm
from students.models import Student
from schools.models import Branch
from .models import ResultComponent,StudentFinalResult
from django.db.models import Q
from academics.models import Session, Term
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from classes.models import Class, Subject
from .models import ResultStructure, ResultComponent, StudentAverageResult,StudentResult
import json
from django.db.models import Sum, Avg, Max, Min
from academics.models import (
    Session, Term
)
from schools.models import Branch
from students.models import Student
from results.models import  StudentFinalResult,StudentAverageResult
from ratings.models import Rating
from attendance.models import StudentAttendance,SchoolDaysOpen
from comments.models import Comment




@login_required_with_short_code
@admin_required
@transaction.atomic
def create_result_structure(request, short_code):
    """
    View to create or update a result structure for a school branch.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    user_roles = get_user_roles(request.user, school)

    if request.method == 'POST':
        form = ResultStructureForm(request.POST, school=school)

        if form.is_valid():
            result_structure = form.save(commit=False)
            result_structure.save()
            messages.success(request, "Result structure created/updated successfully!")
            return redirect('list_result_structures', short_code=short_code)
        else:
            # Debugging: Log form errors
            print(f"DEBUG: Form errors: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResultStructureForm(school=school)

    return render(request, 'results/create_result_structure.html', {
        'form': form,
        'school': school,
        **user_roles,
    })


@login_required_with_short_code
@admin_required
def edit_result_structure(request, short_code, structure_id):
    """
    View to edit a specific result structure.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    result_structure = get_object_or_404(ResultStructure, id=structure_id, branch__school=school)
    user_roles = get_user_roles(request.user, school)

    if request.method == 'POST':
        form = ResultStructureForm(request.POST, instance=result_structure, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, "Result structure updated successfully!")
            return redirect('list_result_structures', short_code=short_code)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResultStructureForm(instance=result_structure, school=school)

    return render(request, 'results/create_result_structure.html', {
        'form': form,
        'result_structure': result_structure,
        'school': school,
        **user_roles,
    })


@login_required_with_short_code
@admin_required
@transaction.atomic
def add_result_components(request, short_code, structure_id):
    """
    View to add or update result components for a specific result structure.
    """
    result_structure = get_object_or_404(ResultStructure, id=structure_id)
    school = result_structure.branch.school
    branch = result_structure.branch
    user_roles = get_user_roles(request.user, school)

    if school.short_code != short_code:
        messages.error(request, "Invalid school or structure.")
        return redirect('list_result_structures', short_code=short_code)

    # Define the formset with the dynamic branch filter
    ComponentFormSet = modelformset_factory(
        ResultComponent,
        form=ResultComponentForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        # Clean the POST data to remove invalid IDs
        cleaned_post_data = QueryDict(request.POST.urlencode(), mutable=True)
        for i in range(int(cleaned_post_data.get('form-TOTAL_FORMS', 0))):
            form_id = cleaned_post_data.get(f'form-{i}-id')
            if form_id == 'None':  # Remove invalid IDs
                cleaned_post_data.pop(f'form-{i}-id', None)

        formset = ComponentFormSet(
            cleaned_post_data,
            queryset=ResultComponent.objects.filter(structure=result_structure),
            form_kwargs={'branch': branch}
        )

        if formset.is_valid():
            components = formset.save(commit=False)
            for component in components:
                component.structure = result_structure
                component.save()

            # Delete removed components
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "Result components updated successfully!")
            return redirect('add_result_components', short_code=short_code, structure_id=structure_id)
        else:
            # Log errors for debugging
            for form in formset:
                if form.is_valid():
                    print(f"DEBUG: Valid form: {form.cleaned_data}")
                else:
                    print(f"DEBUG: Form errors: {form.errors}")
            print(f"DEBUG: Non-form errors: {formset.non_form_errors()}")
            messages.error(request, "Please correct the errors below.")
    else:
        formset = ComponentFormSet(
            queryset=ResultComponent.objects.filter(structure=result_structure),
            form_kwargs={'branch': branch}
        )

    # Filter subjects for the branch
    subjects = Subject.objects.filter(classes__branches=branch).distinct()

    return render(request, 'results/add_result_components.html', {
        'formset': formset,
        'result_structure': result_structure,
        'school': school,
        'subjects': subjects,
        **user_roles,
    })





@login_required_with_short_code
@admin_required
def list_result_structures(request, short_code):
    """
    View to list all result structures for a given school.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    result_structures = ResultStructure.objects.filter(branch__school=school).select_related('branch')
    user_roles = get_user_roles(request.user, school)

    # Pagination
    paginator = Paginator(result_structures, 10)  # Display 10 result structures per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'results/list_result_structures.html', {
        'school': school,
        'result_structures': page_obj,  # Paginated result structures
        **user_roles,
    })




def filter_students_for_scores(request, short_code):
    """
    Render the template for filtering students for score entry.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    user_roles = get_user_roles(request.user, school)

    context = {
        'school': school,
        'sessions': Session.objects.filter(school=school),
        'terms': Term.objects.none(),
        'branches': Branch.objects.filter(school=school),
        **user_roles,
    }
    return render(request, 'results/filter_scores.html', context)


@csrf_exempt
def get_student_scores(request, short_code):
    """
    Fetch students and result components for score entry based on filters.
    Include existing scores for students if available.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            subject_id = data.get("subject")  # This can be None
            class_ids = data.get("classes", [])

            # Validate input fields
            if not session_id or not term_id or not branch_id or not class_ids:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Fetch related objects
            session = get_object_or_404(Session, id=session_id, school=school)
            term = get_object_or_404(Term, id=term_id, session=session)
            branch = get_object_or_404(Branch, id=branch_id, school=school)
            subject = Subject.objects.filter(id=subject_id).first()  # Handle optional subject

            # Fetch result structure for the branch
            result_structure = get_object_or_404(ResultStructure, branch=branch)
            
            # Print conversion total and exam total for debugging
            print(f"DEBUG: Conversion Total is {result_structure.conversion_total}")
            print(f"DEBUG: Exam Total is {result_structure.exam_total}")

            # Fetch students in the selected classes
            students = Student.objects.filter(
                current_session=session,
                branch=branch,
                student_class__id__in=class_ids
            ).select_related('user')

            # Fetch result components for the selected structure
            components = ResultComponent.objects.filter(
                structure=result_structure
            ).filter(
                Q(subject=subject) | Q(subject__isnull=True)  # Include components with no subject
            )

            # Prepare data for the response
            student_data = []
            for student in students:
                # Check if scores exist for this student, subject, session, term, and branch
                final_result = StudentFinalResult.objects.filter(
                    student=student,
                    session=session,
                    term=term,
                    branch=branch,
                    subject=subject,
                    student_class=student.student_class
                ).first()

                student_components = [
                    {
                        "component_id": component.id,
                        "component_name": component.name,
                        "max_marks": component.max_marks,
                        "score": "",  # Placeholder for component score (can be updated if needed)
                    }
                    for component in components
                ]

                student_data.append({
                    "id": student.id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "components": student_components,
                    "converted_ca": final_result.converted_ca if final_result else "",  # Existing CA
                    "exam_score": final_result.exam_score if final_result else "",  # Existing Exam Score
                })

            return JsonResponse({
                "students": student_data,
                "components": [
                    {"id": component.id, "name": component.name, "max_marks": component.max_marks}
                    for component in components
                ],
                "conversion_total": result_structure.conversion_total,  # Pass the conversion total here
                "exam_total": result_structure.exam_total,  # Pass the total exam score here
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)





@transaction.atomic
def save_student_scores(request, short_code):
    """
    Save or update student scores, calculate class-based highest, lowest, and average scores,
    and update student averages.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            subject_id = data.get("subject")
            scores = data.get("scores", [])

            # Validate required fields
            if not session_id or not term_id or not branch_id or not subject_id:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Fetch related objects
            session = Session.objects.get(id=session_id)
            term = Term.objects.get(id=term_id)
            branch = Branch.objects.get(id=branch_id)
            subject = Subject.objects.get(id=subject_id)

            # Process scores and save/update results
            for score in scores:
                student = Student.objects.get(id=score["student_id"])
                student_class = student.student_class  # Fetch the class directly from the student

                if not student_class:
                    return JsonResponse({
                        "error": f"Student {student.id} does not have an associated class."
                    }, status=400)

                total_score = score["converted_ca"] + score["exam_score"]

                # Save or update final results
                StudentFinalResult.objects.update_or_create(
                    student=student,
                    session=session,
                    term=term,
                    branch=branch,
                    student_class=student_class,
                    subject=subject,
                    defaults={
                        "converted_ca": score["converted_ca"],
                        "exam_score": score["exam_score"],
                        "total_score": total_score,
                        "grade": calculate_grade(total_score),
                        "remarks": generate_remark(calculate_grade(total_score)),
                    },
                )

            # Update highest, lowest, and average scores for each class
            classes = Student.objects.filter(
                final_results__session=session,
                final_results__term=term,
                final_results__branch=branch
            ).values_list('student_class', flat=True).distinct()

            for cls in classes:
                update_class_scores(session, term, branch, cls, subject)

            return JsonResponse({"success": True, "message": "Scores saved successfully."})

        except Exception as e:
            return JsonResponse({"error": f"Error: {str(e)}"}, status=500)


def update_class_scores(session, term, branch, student_class, subject):
    """
    Update the highest, lowest (ignoring zero), and average scores for a given class.
    """
    results = StudentFinalResult.objects.filter(
        session=session,
        term=term,
        branch=branch,
        student_class=student_class,
        subject=subject,
    )

    # Calculate the highest, lowest (excluding zeros), and average scores
    highest_score = results.aggregate(Max("total_score"))["total_score__max"] or 0
    lowest_score = results.exclude(total_score=0).aggregate(Min("total_score"))["total_score__min"] or 0
    average_score = results.aggregate(Avg("total_score"))["total_score__avg"] or 0

    # Update all final results for the class
    results.update(
        highest_score=highest_score,
        lowest_score=lowest_score,
        average_score=round(average_score, 2) if average_score else 0,
    )

    # Update student averages for the class
    update_student_averages(session, term, branch, student_class)

    


def update_student_averages(session, term, branch, student_class):
    """
    Calculate and save/update average results for students in a given class.
    """
    students = Student.objects.filter(
        final_results__session=session,
        final_results__term=term,
        final_results__branch=branch,
        student_class=student_class,
    ).distinct()

    for student in students:
        student_results = StudentFinalResult.objects.filter(
            student=student,
            session=session,
            term=term,
            branch=branch,
            student_class=student_class,
        )

        # Calculate total scores
        total_score_obtained = student_results.aggregate(total_obtained=Sum("total_score"))["total_obtained"] or 0
        total_subjects = student_results.count()
        total_score_maximum = total_subjects * 100  # Assuming max score per subject is 100

        # Save or update average results
        StudentAverageResult.objects.update_or_create(
            student=student,
            session=session,
            term=term,
            branch=branch,
            defaults={
                "total_score_obtained": total_score_obtained,
                "total_score_maximum": total_score_maximum,
                "average_percentage": (total_score_obtained / total_score_maximum) * 100
                if total_score_maximum > 0
                else 0,
            },
        )


def calculate_grade(total_score):
    """
    Calculate grade based on total score following the A1, B2 standard.
    """
    if total_score >= 75:
        return "A1"  # Excellent
    elif total_score >= 70:
        return "B2"  # Very Good
    elif total_score >= 65:
        return "B3"  # Good
    elif total_score >= 60:
        return "C4"  # Credit
    elif total_score >= 55:
        return "C5"  # Credit
    elif total_score >= 50:
        return "C6"  # Credit
    elif total_score >= 45:
        return "D7"  # Pass
    elif total_score >= 40:
        return "E8"  # Pass
    else:
        return "F9"  # Fail


def generate_remark(grade):
    """
    Generate a remark based on the grade.
    """
    remarks = {
        "A1": "Excellent",
        "B2": "Very Good",
        "B3": "Good",
        "C4": "Credit",
        "C5": "Credit",
        "C6": "Credit",
        "D7": "Pass",
        "E8": "Pass",
        "F9": "Fail",
    }
    return remarks.get(grade, "No Remark Available")

import random

def get_comment_by_percentage(percentage):
    comments = {
        75: [
            "Excellent work, keep it up!",
            "Outstanding performance, you're doing great!",
            "You did good, fantastic job!",
            "Your performance is remarkable, keep it consistent!",
            "Incredible effort, you're a role model!",
            "Great job, your dedication is paying off!",
            "Superb work, you're achieving excellence!",
            "Amazing results, you're on the right path!",
            "You're at the top, keep leading the way!",
            "Fantastic effort, you're setting an example!"
        ],
        70: [
            "Very good job, keep up the great work!",
            "You're doing well, aim a little higher!",
            "Nice effort, you're almost there!",
            "Impressive performance, keep progressing!",
            "You're on the right track, stay focused!",
            "Great progress, you're improving steadily!",
            "Well done, you’re doing great!",
            "You're achieving good results, keep it up!",
            "Good job, keep pushing forward!",
            "You're performing well, aim for the top!"
        ],
        65: [
            "Good effort, you’re improving!",
            "You're doing fine, keep working harder!",
            "Nice progress, you're getting there!",
            "Good job, but there's room to grow!",
            "Keep going, you're on the right path!",
            "Steady improvement, keep it consistent!",
            "You're achieving fair results, aim for better!",
            "Good performance, push yourself more!",
            "Well done, but you can aim higher!",
            "You're improving, don't lose momentum!"
        ],
        50: [
            "Fair performance, but you can do better!",
            "You're making progress, keep at it!",
            "Not bad, but there's room for improvement.",
            "You're doing okay, but aim higher!",
            "Decent effort, strive for more next time!",
            "You're getting there, keep trying harder!",
            "Fair work, but there's potential for more!",
            "You're doing fine, push yourself further!",
            "Good attempt, aim for greater heights!",
            "Keep improving, you’re on the right track!"
        ],
        40: [
            "You're passing, but strive for better results!",
            "You're capable of more, work harder!",
            "Not bad, but you can do better with effort.",
            "You're just making it, aim for higher scores!",
            "Keep trying, you're on the brink of improvement!",
            "You're getting through, but there's room for growth.",
            "Put in more effort to see greater results!",
            "You're close, but push for a better grade!",
            "You're passing, but aim higher next time.",
            "A fair attempt, but there's potential for improvement."
        ],
        0: [
            "Poor performance, you need to work harder.",
            "Don't lose hope, keep trying!",
            "This isn't your best, you can improve!",
            "You're struggling, but success is within reach.",
            "Failure is a step to success, keep working!",
            "Not good enough, but you can rise above this.",
            "Keep going, you're capable of much more!",
            "Focus and determination will help you improve.",
            "You need to put in more effort to succeed.",
            "Don't give up, you can turn this around!"
        ]
    }

    if percentage >= 75:
        return random.choice(comments[75])
    elif percentage >= 70:
        return random.choice(comments[70])
    elif percentage >= 65:
        return random.choice(comments[65])
    elif percentage >= 50:
        return random.choice(comments[50])
    elif percentage >= 40:
        return random.choice(comments[40])
    else:
        return random.choice(comments[0])




def render_class_result_preview(request, short_code):
    """
    Render the class result preview template.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    user_roles = get_user_roles(request.user, school)


    context = {
        'school': school,
        'sessions': Session.objects.filter(school=school),
        'terms': Term.objects.none(),
        'branches': Branch.objects.filter(school=school),
        **user_roles,
    }
    return render(request, "results/class_result_preview.html", context)

@csrf_exempt
def fetch_class_results(request, short_code):
    """
    Fetch and filter class results dynamically based on entered parameters.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            class_ids = data.get("classes", [])

            # Validate required parameters
            if not (session_id and term_id and branch_id and class_ids):
                return JsonResponse({"error": "Missing required filters."}, status=400)

            # Fetch related objects
            session = Session.objects.get(id=session_id)
            term = Term.objects.get(id=term_id)
            branch = Branch.objects.get(id=branch_id)

            # Fetch students and their results
            students = Student.objects.filter(
                student_class__id__in=class_ids,
                branch=branch
            ).select_related("user")

            results = StudentFinalResult.objects.filter(
                session=session,
                term=term,
                branch=branch,
                student_class__id__in=class_ids
            ).select_related("subject", "student").order_by("student__last_name", "subject__name")

            # Group results by student and subject
            grouped_results = {}
            for result in results:
                if result.student_id not in grouped_results:
                    grouped_results[result.student_id] = {
                        "student": result.student,
                        "subjects": []
                    }
                grouped_results[result.student_id]["subjects"].append({
                    "subject": result.subject.name,
                    "converted_ca": result.converted_ca,
                    "exam_score": result.exam_score,
                    "total_score": result.total_score,
                    "grade": result.grade
                })

            # Prepare data for response
            response_data = {
                "students": [
                    {
                        "student_id": student_id,
                        "student_name": f"{data['student'].first_name} {data['student'].last_name}",
                        "subjects": data["subjects"]
                    }
                    for student_id, data in grouped_results.items()
                ]
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            print(f"Error occurred: {e}")
            return JsonResponse({"error": f"Error: {str(e)}"}, status=500)


from django.db.models import Value, CharField
def render_generate_result_filter(request, short_code):
    """
    Render the result generation filter template.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    user_roles = get_user_roles(request.user, school)
    branches = [
        {
            "id": branch.id,
            "branch_name": branch.branch_name,
            "school_type": "Primary" if branch.primary_school else "Secondary"
        }
        for branch in Branch.objects.filter(school=school)
    ]


    context = {
        'school': school,
        'sessions': Session.objects.filter(school=school),
        'terms': Term.objects.none(),  # Initially empty, dynamically loaded
        'branches': branches,
        **user_roles,
    }
    return render(request, "results/generate_result_filter.html", context)



@csrf_exempt
def fetch_students_result(request, short_code):
    """
    Fetch detailed student results, including name, class, attendance count, scores for each subject,
    average, comments, ratings, branch details, times absent, remarks for each grade,
    total number of subjects, total number of subjects failed, highest, lowest, and average scores,
    along with principal/headteacher comments, term information, and next term begins date.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            class_ids = data.get("classes", [])

            # Validate required parameters
            if not (session_id and term_id and branch_id and class_ids):
                return JsonResponse({"error": "Missing required filters."}, status=400)

            # Fetch related objects
            session = get_object_or_404(Session, id=session_id)
            term = get_object_or_404(Term, id=term_id)
            branch = get_object_or_404(Branch, id=branch_id)
            school = branch.primary_school or branch.school

            # Fetch email and phone number from SchoolRegistration
            school_registration = get_object_or_404(SchoolRegistration, short_code=short_code)
            school_email = school_registration.email
            school_phone = school_registration.admin_phone_number

            # Determine if the school is primary or secondary
            school_type = "Primary" if branch.primary_school else "Secondary"
            school_name = school.school_name
            school_address = branch.address  # Use branch's address

            # Determine the term label based on term_name
            term_label_map = {
                "First Term": "FIRST TERM EXAMINATION REPORT",
                "Second Term": "SECOND TERM EXAMINATION REPORT",
                "Third Term": "THIRD TERM EXAMINATION REPORT",
            }
            term_label = term_label_map.get(term.term_name, "TERM EXAMINATION REPORT")

            # Determine next term begins date
            next_term_start_date = None
            if term.term_name == "First Term":
                next_term = Term.objects.filter(session=session, term_name="Second Term").first()
                if next_term:
                    next_term_start_date = next_term.start_date
            elif term.term_name == "Second Term":
                next_term = Term.objects.filter(session=session, term_name="Third Term").first()
                if next_term:
                    next_term_start_date = next_term.start_date
            elif term.term_name == "Third Term":
                next_session = Session.objects.filter(id__gt=session.id).order_by("id").first()
                if next_session:
                    next_term = Term.objects.filter(session=next_session, term_name="First Term").first()
                    if next_term:
                        next_term_start_date = next_term.start_date

            # Format the next term date if available
            formatted_next_term_start_date = (
                next_term_start_date.strftime("%B %d, %Y") if next_term_start_date else "Not Available"
            )

            # Fetch total days the school was open for the session and term
            total_days_open = SchoolDaysOpen.objects.filter(
                branch=branch, session=session, term=term
            ).values_list('days_open', flat=True).first() or 0

            # Fetch students in the selected classes and branch
            students = Student.objects.filter(
                student_class__id__in=class_ids,
                branch=branch
            ).select_related("user", "student_class")

            # Fetch attendance, averages, and ratings
            attendance_counts = StudentAttendance.objects.filter(
                session=session, term=term, branch=branch, student__in=students
            ).values("student").annotate(total_attendance=Sum("attendance_count"))

            averages = StudentAverageResult.objects.filter(
                session=session, term=term, branch=branch, student__in=students
            ).select_related("student")

            comments = Comment.objects.filter(
                session=session, term=term, student__in=students
            ).select_related("student", "author")

            # Fetch results for the students
            results = StudentFinalResult.objects.filter(
                session=session,
                term=term,
                branch=branch,
                student_class__id__in=class_ids
            ).select_related("subject", "student").order_by("student__last_name", "subject__name")

            # Group results by student
            grouped_results = {}
            for result in results:
                # Skip subjects where both CA and exam scores are zero
                if result.converted_ca == 0 and result.exam_score == 0:
                    continue

                if result.student_id not in grouped_results:
                    attendance = next(
                        (item["total_attendance"] for item in attendance_counts if item["student"] == result.student_id), 0
                    )
                    avg_result = next(
                        (
                            {
                                "total_score_obtained": round(avg.total_score_obtained, 2),
                                "average_percentage": round(avg.average_percentage, 2)
                            }
                            for avg in averages if avg.student_id == result.student_id
                        ), {}
                    )
                    average_percentage = avg_result.get("average_percentage", 0)

                    # Use `get_comment_by_percentage` for principal/headteacher comments
                    principal_comment = get_comment_by_percentage(average_percentage)

                    # Fetch profile picture
                    profile_picture = (
                        result.student.profile_picture.url
                        if hasattr(result.student, "profile_picture") and result.student.profile_picture
                        else result.student.user.profile_picture.url
                        if hasattr(result.student.user, "profile_picture") and result.student.user.profile_picture
                        else None
                    )
                    # Fetch psychomotor and behavioral ratings for the student
                    psychomotor_rating = Rating.objects.filter(
                    rating_type='psychomotor',
                    session=session, 
                    term=term,
                    branch=branch,
                    student__in=students
                    ).select_related("student").first()  


                    behavioral_rating = Rating.objects.filter(
                    rating_type='behavioral',
                    session=session, 
                    term=term, 
                    branch=branch, 
                    student__in=students
                    ).select_related("student").first()  


                    grouped_results[result.student_id] = {
                        "first_name": result.student.first_name,
                        "last_name": result.student.last_name,
                        "profile_picture": profile_picture,
                        "class": result.student.student_class.name,
                        "attendance_count": attendance,
                        "times_absent": max(0, total_days_open - attendance),  # Calculate times absent
                        "total_days_school_opened": total_days_open,
                        "subjects": [],
                        "total_subjects": 0,
                        "subjects_failed": 0,
                        "subjects_passed": 0,
                        "highest_score": None,
                        "lowest_score": None,
                        "average_score": None,
                        "average": avg_result,
                        "rating": {
                            "psychomotor": {
                                "coordination": psychomotor_rating.coordination if psychomotor_rating else "N/A",
                                "handwriting": psychomotor_rating.handwriting if psychomotor_rating else "N/A",
                                "sports": psychomotor_rating.sports if psychomotor_rating else "N/A",
                                "artistry": psychomotor_rating.artistry if psychomotor_rating else "N/A",
                                "verbal_fluency": psychomotor_rating.verbal_fluency if psychomotor_rating else "N/A",
                                "games": psychomotor_rating.games if psychomotor_rating else "N/A",
                            },
                            "behavioral": {
                                "punctuality": behavioral_rating.punctuality if behavioral_rating else "N/A",
                                "attentiveness": behavioral_rating.attentiveness if behavioral_rating else "N/A",
                                "obedience": behavioral_rating.obedience if behavioral_rating else "N/A",
                                "leadership": behavioral_rating.leadership if behavioral_rating else "N/A",
                                "emotional_stability": behavioral_rating.emotional_stability if behavioral_rating else "N/A",
                                "teamwork": behavioral_rating.teamwork if behavioral_rating else "N/A",
                            }
                        },

                        "comments": [
                            {
                                "author": comment.author.get_full_name(),
                                "text": comment.comment_text,
                                "date": comment.created_at
                            }
                            for comment in comments if comment.student_id == result.student_id
                        ],
                        "max_obtainable_score": 100 * results.filter(student_id=result.student_id).count(),
                        "obtained_score": round(
                            results.filter(student_id=result.student_id).aggregate(Sum("total_score"))["total_score__sum"] or 0,
                            2
                        ),
                        "principal_comment": principal_comment
                    }

                # Add subject details
                grouped_results[result.student_id]["total_subjects"] += 1
                grouped_results[result.student_id]["subjects"].append({
                    "subject": result.subject.name,
                    "converted_ca": result.converted_ca,
                    "exam_score": result.exam_score,
                    "total_score": result.total_score,
                    "grade": result.grade,
                    "remark": generate_remark(result.grade),  # Use the grading function here
                    "highest_score": result.highest_score,  # From database
                    "lowest_score": result.lowest_score,    # From database
                    "average_score": round(result.average_score, 2) if result.average_score else None  # From database
                })

                # Increment subjects passed and failed
                if result.grade == "F9":  # Assuming F9 is the failing grade
                    grouped_results[result.student_id]["subjects_failed"] += 1
                else:
                    grouped_results[result.student_id]["subjects_passed"] += 1

            # Sort students by highest percentage to lowest
            sorted_students = sorted(
                grouped_results.values(),
                key=lambda x: x["average"]["average_percentage"],
                reverse=True
            )

            # Prepare response data
            response_data = {
                "school_details": {
                    "school_name": school_name,
                    "school_type": school_type,
                    "school_address": school_address,
                    "school_email": school_email,
                    "school_phone": school_phone,
                    "logo": school.logo.url if school.logo else None,
                    "term_label": term_label,
                    "next_term_begins": formatted_next_term_start_date  # Include next term begins
                },
                "students": sorted_students
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            print(f"Error occurred: {e}")
            return JsonResponse({"error": f"Error: {str(e)}"}, status=500)
