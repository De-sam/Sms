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
from students.models import Student,ParentStudentRelationship
from results.models import  StudentFinalResult,StudentAverageResult
from ratings.models import Rating
from attendance.models import StudentAttendance,SchoolDaysOpen
from comments.models import Comment
from .models import PublishedResult, GradingSystem
from .models import GradingSystem, Branch



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

            # Fetch students in the selected classes, ordered alphabetically
            students = Student.objects.filter(
                current_session=session,
                branch=branch,
                student_class__id__in=class_ids
            ).select_related('user').order_by('last_name', 'first_name')

            # Fetch result components for the selected structure and subject
            components = ResultComponent.objects.filter(
                structure=result_structure
            ).filter(
                Q(subject=subject) | Q(subject__isnull=True)  # Include components with no subject
            )

            # Prepare data for the response
            student_data = []
            for student in students:
                # Fetch component scores for the student and subject
                component_scores = {
                    sr.component.id: sr.score
                    for sr in StudentResult.objects.filter(
                        student=student,
                        component__in=components,
                        subject=subject  # Ensure scores are filtered by subject
                    )
                }

                student_components = [
                    {
                        "component_id": component.id,
                        "component_name": component.name,
                        "max_marks": component.max_marks,
                        "score": component_scores.get(component.id, ""),  # Use existing score or empty
                    }
                    for component in components
                ]

                # Check if scores exist for this student, subject, session, term, and branch
                final_result = StudentFinalResult.objects.filter(
                    student=student,
                    session=session,
                    term=term,
                    branch=branch,
                    subject=subject,
                    student_class=student.student_class
                ).first()

                student_data.append({
                    "id": student.id,
                    "last_name": student.last_name,
                    "first_name": student.first_name,
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
    Save or update student scores, including component scores, calculate class-based statistics,
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

                # Save or update component scores
                for component_key, component_score in score.items():
                    if component_key.startswith("component_"):
                        component_id = component_key.split("_")[1]  # Extract component ID
                        component = ResultComponent.objects.get(id=component_id)

                        # Ensure the component matches the subject if subject-specific
                        if component.subject and component.subject.id != subject.id:
                            return JsonResponse({
                                "error": f"Component {component.name} is not associated with subject {subject.name}."
                            }, status=400)

                        StudentResult.objects.update_or_create(
                            student=student,
                            component=component,
                            subject=subject,  # Associate the component score with the subject
                            defaults={"score": component_score},
                        )

                # Calculate total component score
                total_component_score = StudentResult.objects.filter(
                    student=student,
                    subject=subject,
                    component__structure__branch=branch  # Ensure same branch
                ).aggregate(Sum("score"))["score__sum"] or 0

                # Calculate converted CA
                result_structure = ResultStructure.objects.get(branch=branch)
                max_component_score = ResultComponent.objects.filter(
                    structure=result_structure
                ).aggregate(Sum("max_marks"))["max_marks__sum"] or 1  # Avoid division by zero

                converted_ca = (total_component_score / max_component_score) * result_structure.conversion_total

                # Calculate total score
                exam_score = score.get("exam_score", 0)
                total_score = round(converted_ca + exam_score, 2)

                # Fetch grade and remark using the database-based logic
                grade, remark = get_grade_and_remark(total_score, branch)  # Pass branch here


                # Save or update final results
                StudentFinalResult.objects.update_or_create(
                    student=student,
                    session=session,
                    term=term,
                    branch=branch,
                    student_class=student_class,
                    subject=subject,
                    defaults={
                        "converted_ca": round(converted_ca, 2),
                        "exam_score": exam_score,
                        "total_score": total_score,
                        "grade": grade,
                        "remarks": remark,  
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
    # Filter results to include only those with valid scores
        student_results = StudentFinalResult.objects.filter(
            student=student,
            session=session,
            term=term,
            branch=branch,
            student_class=student_class,
            converted_ca__gt=0,  # Ensure test scores are valid
            exam_score__gt=0  # Ensure exam scores are valid
        )

        # Aggregate total scores
        total_score_obtained = student_results.aggregate(total_obtained=Sum("total_score"))["total_obtained"] or 0

        # Count the number of subjects with valid scores
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


def get_grade_and_remark(total_score, branch):
    """
    Fetch grade and remark from the database if available.
    Use default functions as a fallback.
    """
    # Check for grading system in the database
    grading_system = GradingSystem.objects.filter(branch=branch).order_by('-lower_bound')

    # Use grading system from database if available
    for grade_entry in grading_system:
        if grade_entry.lower_bound <= total_score <= grade_entry.upper_bound:
            return grade_entry.grade, grade_entry.remark

    # Fallback to default calculation
    grade = calculate_grade(total_score)
    remark = generate_remark(grade)
    return grade, remark


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

            # Check if the user is a student
            is_student = hasattr(request.user, 'student_profile')

            if is_student:
                # Get the logged-in student's profile
                student = request.user.student_profile

                # Override branch and class filters for the student
                branch_id = student.branch.id
                class_ids = [student.student_class.id]

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


from django.urls import resolve

def render_generate_result_filter(request, short_code):
    """
    Render the result generation filter template based on the request path.
    If the request is for fetching results, use "generate_result_filter.html".
    If the request is for fetching broadsheet, use "broadsheet.html".
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    user_roles = get_user_roles(request.user, school)

    # Default values
    student_branch = None
    student_class = None
    parent_branches = []
    parent_classes = []

    # Determine if the user is a student
    if hasattr(request.user, 'student_profile'):
        student_branch = request.user.student_profile.branch
        student_class = request.user.student_profile.student_class

    # Determine if the user is a parent
    if hasattr(request.user, 'parent_profile'):
        parent_relationships = ParentStudentRelationship.objects.filter(
            parent_guardian=request.user.parent_profile,
            student__branch__school=school
        )
        # Get distinct branches and classes linked to the parent's children
        parent_branches = [
            {
                "id": branch.id,
                "branch_name": branch.branch_name,
                "school_type": "Primary" if branch.primary_school else "Secondary"
            }
            for branch in Branch.objects.filter(
                id__in=parent_relationships.values_list('student__branch_id', flat=True)
            ).distinct()
        ]
        parent_classes = Class.objects.filter(
            id__in=parent_relationships.values_list('student__student_class_id', flat=True)
        ).distinct()

    # Prepare all branches for admins
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
        'branches': branches,  # For admins
        'classes': Class.objects.filter(branches__school=school),  # For admins
        'student_branch': student_branch,  # Pre-fill for students
        'student_class': student_class,  # Pre-fill for students
        'parent_branches': parent_branches,  # Pre-fill for parents
        'parent_classes': parent_classes,  # Pre-fill for parents
        'is_school_admin': 'is_school_admin' in user_roles,
        'is_student': 'is_student' in user_roles,
        'is_parent': 'is_parent' in user_roles,
        **user_roles,  # Include additional roles for flexibility
    }

    # Determine which template to render based on URL name
    url_name = resolve(request.path_info).url_name
    if url_name == "fetch_students_broadsheet":
        template = "results/broadsheet.html"
    else:
        template = "results/generate_result_filter.html"

    return render(request, template, context)



@csrf_exempt
def fetch_students_result(request, short_code):
    """
    Fetch detailed student results for admins, students, and parents, including 
    filtering based on roles and the specific classes or branches relevant to the user.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            class_ids = data.get("classes", [])
            school = get_object_or_404(SchoolRegistration, short_code=short_code)

            # Determine user roles
            is_student = hasattr(request.user, 'student_profile')
            is_admin = request.user == school.admin_user
            is_parent = hasattr(request.user, 'parent_profile')

            if is_student:
                # Get the logged-in student's profile
                student = request.user.student_profile

                # Override branch and class filters for the student
                branch_id = student.branch.id
                class_ids = [student.student_class.id]

            elif is_parent:
                # Filter results based on the parent's children
                parent_relationships = ParentStudentRelationship.objects.filter(
                    parent_guardian=request.user.parent_profile,
                    student__branch_id=branch_id  # Ensure the branch matches the selected branch
                )

                # Restrict classes to those of the parent's children
                parent_class_ids = parent_relationships.values_list(
                    'student__student_class_id', flat=True
                ).distinct()

                # Validate the selected classes against the parent's children
                if not set(class_ids).issubset(set(parent_class_ids)):
                    return JsonResponse({"error": "You are not authorized to view results for the selected classes."}, status=403)

            # Validate required parameters
            if not (session_id and term_id and branch_id and class_ids):
                return JsonResponse({"error": "Missing required filters."}, status=400)

            # Check if results are published (Skip check for admins)
            if not is_admin:
                published = PublishedResult.objects.filter(
                    session_id=session_id,
                    term_id=term_id,
                    branch_id=branch_id,
                    cls_id__in=class_ids,  # Ensure class filtering
                    is_published=True
                ).exists()

                if not published:
                    return JsonResponse(
                        {"error": "Results are not yet published for the selected term."},
                        status=403
                    )


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

            # Include session in the term label
            session_year = session.session_name  # Fetch session name (e.g., "2023/24")
            term_label_map = {
                "First Term": "FIRST TERM EXAMINATION REPORT",
                "Second Term": "SECOND TERM EXAMINATION REPORT",
                "Third Term": "THIRD TERM EXAMINATION REPORT",
            }

            term_label = f"{term.term_name.upper()} ACADEMIC REPORT - {session_year} ACADEMIC SESSION"
            
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

            # If the user is a student, filter down to only their results
            if is_student:
                students = students.filter(user=request.user)
                print(f"Filtered students for {request.user}: {students}")
            elif is_parent:
                students = students.filter(
                    id__in=parent_relationships.values_list('student_id', flat=True)
                )
                print(f"Filtered students for parent {request.user}: {students}")

   
            else:
                students = Student.objects.filter(
                     student_class__id__in=class_ids,
                         branch=branch
                 )
                print(f"Admin fetching results: {students}")

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
                student_class__id__in=class_ids,
                student__in=students
            ).select_related("subject", "student").order_by("student__last_name", "subject__name")

            # Group results by student
            grouped_results = {}
            for result in results:
                # Skip subjects where both CA and exam scores are zero
                if result.converted_ca == 0 and result.exam_score == 0:
                    continue
                
                # Ensure the branch is available for the result
                branch = result.branch

                # Fetch grade and remark dynamically
                grade, remark = get_grade_and_remark(result.total_score, branch)

                # Update result object if needed (optional)
                result.grade = grade
                result.remarks = remark
                result.save()

                
                if result.student_id not in grouped_results:
                    attendance = next(
                        (item["total_attendance"] for item in attendance_counts if item["student"] == result.student_id), 0
                    )
                    avg_result = averages.filter(student_id=result.student_id).first()

                    average_percentage = (
                        round(avg_result.average_percentage, 2)
                        if avg_result and avg_result.average_percentage is not None
                        else 0
                    )
                    
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
                    psychomotor_ratings = Rating.objects.filter(
                        student=result.student,
                        branch=branch,
                        session=session,
                        term=term,
                        rating_type="psychomotor"
                    )

                    behavioral_ratings = Rating.objects.filter(
                        student=result.student,
                        branch=branch,
                        session=session,
                        term=term,
                        rating_type="behavioral"
                    )

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
                        "average": {
                            "total_score_obtained": avg_result.total_score_obtained if avg_result else 0,
                            "total_score_maximum": avg_result.total_score_maximum if avg_result else 0,
                            "average_percentage": average_percentage,
                        },
                        "ratings": {
                            "psychomotor": [rating.to_dict() for rating in psychomotor_ratings],
                            "behavioral": [rating.to_dict() for rating in behavioral_ratings],
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
                    "grade": grade,  # Add grade here
                    "remark": remark, # Use the grading function here
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


@csrf_exempt
def fetch_results_wrapper(request, short_code):
    """
    Handles both GET requests for rendering templates and POST requests for fetching data.
    """
    if request.method == "GET":
        # Determine which template to render
        school = get_object_or_404(SchoolRegistration, short_code=short_code)
        url_name = resolve(request.path_info).url_name
        
        if url_name == "fetch_students_broadsheet":
            template = "results/broadsheet.html"
        else:
            template = "results/generate_result_filter.html"

        # Fetch branches and include branch type (Primary/Secondary)
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
            'branches': branches,  # List of branches with type
            'classes': Class.objects.filter(branches__school=school),  # For admins
        }

        return render(request, template, context)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)

            # Log incoming data for debugging
            print(f"Incoming data: {data}")

            # Check user type
            is_student = hasattr(request.user, 'student_profile')
            is_parent = hasattr(request.user, 'parent_profile')

            if is_student:
                student = request.user.student_profile
                data["branch"] = student.branch.id
                data["classes"] = [student.student_class.id]
                print(f"Modified data for student: {data}")

            elif is_parent:
                # Handle parent-specific filtering
                parent_relationships = ParentStudentRelationship.objects.filter(
                    parent_guardian=request.user.parent_profile,
                    student__branch_id=data.get("branch")  # Ensure the branch matches a selected branch
                )

                # Collect unique class IDs linked to the parent's children
                parent_classes = parent_relationships.values_list('student__student_class_id', flat=True).distinct()
                if not parent_classes:
                    return JsonResponse({"error": "No classes found for the selected branch."}, status=400)

                data["classes"] = list(parent_classes)
                print(f"Modified data for parent: {data}")

            # Serialize back to request body
            request._body = json.dumps(data)
            return fetch_students_result(request, short_code)

        except Exception as e:
            # Log error for debugging
            print(f"Error in fetch_results_wrapper: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@login_required_with_short_code
@admin_required
@transaction.atomic
def publish_results(request, short_code):
    """
    Publish results for a specific session, term, branch, and class(es).
    """
    if request.method == "POST":
        data = json.loads(request.body)  # Parse JSON payload

        session_id = data.get("session")
        term_id = data.get("term")
        branch_id = data.get("branch")
        class_ids = data.get("classes", [])  # List of classes

        if not all([session_id, term_id, branch_id]) or not class_ids:
            return JsonResponse({'success': False, 'error': 'Missing required data.'}, status=400)

        # Fetch the required objects
        session = get_object_or_404(Session, id=session_id)
        term = get_object_or_404(Term, id=term_id)
        branch = get_object_or_404(Branch, id=branch_id)

        # Loop through each class_id to publish results
        for class_id in class_ids:
            cls = get_object_or_404(Class, id=class_id)

            # Update or create the published record
            published_result, created = PublishedResult.objects.get_or_create(
                session=session, term=term, branch=branch, cls=cls
            )

            if not published_result.is_published:
                published_result.is_published = True
                published_result.save()

        return JsonResponse({'success': True, 'message': 'Results published successfully!'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)



def list_published_results(request, short_code):
    """
    Display a paginated table of published results for the admin.
    Includes branch type and department if available.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    user_roles = get_user_roles(request.user, school)

    # Fetch all published results related to the school
    published_results = PublishedResult.objects.filter(
        branch__school=school
    ).select_related('session', 'term', 'branch', 'cls').order_by('-published_at')

    # Annotate branch type dynamically
    for result in published_results:
        result.branch_type = "Primary" if result.branch.primary_school else "Secondary"
        result.department = getattr(result.cls, "department", "N/A")  # If no department, set to 'N/A'

    # Pagination setup (10 records per page)
    paginator = Paginator(published_results, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'school': school,
        'published_results': page_obj,  # Paginated results
        **user_roles,
    }
    return render(request, 'results/list_published_results.html', context)

@login_required_with_short_code
@admin_required
@transaction.atomic
def manage_grading_system(request, short_code):
    """
    View to manage grading systems for a school's branches.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)
    user_roles = get_user_roles(request.user, school)

    selected_branch = None
    grading_systems = []
    branch_type = None  # Initialize branch type

    if request.method == 'POST':
        branch_id = request.POST.get('branch')
        selected_branch = get_object_or_404(Branch, id=branch_id, school=school)

        # Handle grading system entries manually
        lower_bounds = request.POST.getlist('lower_bound')
        upper_bounds = request.POST.getlist('upper_bound')
        grades = request.POST.getlist('grade')
        remarks = request.POST.getlist('remark')

        # Validate and save grading system entries
        for lower, upper, grade, remark in zip(lower_bounds, upper_bounds, grades, remarks):
            if lower and upper and grade:  # Ensure required fields are filled
                GradingSystem.objects.update_or_create(
                    branch=selected_branch,
                    grade=grade,
                    defaults={
                        'lower_bound': lower,
                        'upper_bound': upper,
                        'remark': remark,
                    },
                )

        messages.success(request, f"Grading system for {selected_branch.branch_name} updated successfully!")
    else:
        branch_id = request.GET.get('branch')
        if branch_id:
            selected_branch = get_object_or_404(Branch, id=branch_id, school=school)
            grading_systems = GradingSystem.objects.filter(branch=selected_branch)

            # Determine the branch type (Primary or Secondary)
            if selected_branch.primary_school:
                branch_type = "Primary"
            else:
                branch_type = "Secondary"

    return render(request, 'results/manage_grading_system.html', {
        'school': school,
        'branches': branches,
        'selected_branch': selected_branch,
        'grading_systems': grading_systems,
        'branch_type': branch_type,  # Include branch type in the context
        **user_roles,
    })
