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
from .models import ResultStructure, ResultComponent, StudentResult
import json
from django.db.models import Max, Min

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
                student_components = [
                    {
                        "component_id": component.id,
                        "component_name": component.name,
                        "max_marks": component.max_marks,
                        "score": "",  # Placeholder for score input
                    }
                    for component in components
                ]

                student_data.append({
                    "id": student.id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "components": student_components,
                    "converted_ca": "",  # Placeholder for converted CA
                    "exam_score": ""  # Placeholder for exam score
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



@csrf_exempt
@transaction.atomic
def save_student_scores(request, short_code):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            subject_id = data.get("subject")
            scores = data.get("scores", [])

            if not session_id or not term_id or not branch_id or not subject_id:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Fetch related objects
            session = Session.objects.only('id').get(id=session_id)
            term = Term.objects.only('id').get(id=term_id)
            branch = Branch.objects.only('id').get(id=branch_id)
            subject = Subject.objects.only('id').get(id=subject_id)
            result_structure = ResultStructure.objects.only('id', 'conversion_total', 'exam_total').get(branch=branch)

            # Fetch components for the structure and subject
            components = ResultComponent.objects.filter(
                structure=result_structure
            ).filter(
                Q(subject=subject) | Q(subject__isnull=True)
            ).only('id', 'max_marks')

            # Pre-compute max_score for all components
            max_score = sum([component.max_marks for component in components])
            conversion_total = result_structure.conversion_total

            # Prepare component ID to max marks mapping for fast lookups
            component_max_marks = {component.id: component.max_marks for component in components}

            for score in scores:
                student_id = score.get("student_id")
                submitted_converted_ca = float(score.get("converted_ca", 0))
                exam_score = float(score.get("exam_score", 0))

                # Extract component scores from the payload
                component_scores = {
                    int(key.split("_")[1]): value for key, value in score.items() if key.startswith("component_")
                }

                # Recalculate Converted CA
                total_score = sum(component_scores.values())
                recalculated_converted_ca = (total_score / max_score) * conversion_total if max_score > 0 else 0

                # Validate the recalculated score
                if round(recalculated_converted_ca, 2) != round(submitted_converted_ca, 2):
                    return JsonResponse({
                        "error": f"Validation failed for student ID {student_id}. Converted CA mismatch."
                    }, status=400)

                # Fetch or create the final result record
                student = Student.objects.only('id').get(id=student_id)
                final_result, created = StudentFinalResult.objects.update_or_create(
                    student=student,
                    session=session,
                    term=term,
                    branch=branch,
                    subject=subject,
                    defaults={
                        "converted_ca": recalculated_converted_ca,
                        "exam_score": exam_score,
                        "total_score": recalculated_converted_ca + exam_score,
                        "grade": calculate_grade(recalculated_converted_ca + exam_score),
                        "remarks": generate_remark(calculate_grade(recalculated_converted_ca + exam_score)),
                    },
                )

                # Update or create component scores
                for component_id, score_value in component_scores.items():
                    StudentResult.objects.update_or_create(
                        student=student,
                        component_id=component_id,
                        defaults={
                            "score": score_value,
                            "converted_ca": recalculated_converted_ca,
                            "exam_score": exam_score,
                            "total_score": recalculated_converted_ca + exam_score,
                        }
                    )

            # Update highest, lowest, and average scores for the subject
            highest_score = get_highest_score(subject_id, session_id, term_id, branch_id)
            lowest_score = get_lowest_score(subject_id, session_id, term_id, branch_id)
            average_score = get_average_score(subject_id, session_id, term_id, branch_id)

            # Update the aggregate fields in the `StudentFinalResult` model
            StudentFinalResult.objects.filter(
                session=session, term=term, branch=branch, subject=subject
            ).update(
                highest_score=highest_score,
                lowest_score=lowest_score,
                average_score=average_score,
            )

            return JsonResponse({"success": True, "message": "Scores saved successfully."})

        except Exception as e:
            print(f"Error saving student scores: {str(e)}")
            return JsonResponse({"error": "An unexpected error occurred."}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


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



def get_highest_score(subject_id, session_id=None, term_id=None, branch_id=None):
    """
    Get the highest score for a specific subject.
    
    :param subject_id: ID of the subject
    :param session_id: (Optional) ID of the session
    :param term_id: (Optional) ID of the term
    :param branch_id: (Optional) ID of the branch
    :return: The highest score or None if no results are found
    """
    filters = {'subject_id': subject_id}
    
    if session_id:
        filters['session_id'] = session_id
    if term_id:
        filters['term_id'] = term_id
    if branch_id:
        filters['branch_id'] = branch_id

    highest_score = StudentFinalResult.objects.filter(**filters).aggregate(Max('total_score'))['total_score__max']
    return highest_score


def get_lowest_score(subject_id, session_id=None, term_id=None, branch_id=None):
    """
    Get the lowest score for a specific subject.
    
    :param subject_id: ID of the subject
    :param session_id: (Optional) ID of the session
    :param term_id: (Optional) ID of the term
    :param branch_id: (Optional) ID of the branch
    :return: The lowest score or None if no results are found
    """
    filters = {'subject_id': subject_id}
    
    if session_id:
        filters['session_id'] = session_id
    if term_id:
        filters['term_id'] = term_id
    if branch_id:
        filters['branch_id'] = branch_id

    lowest_score = StudentFinalResult.objects.filter(**filters).aggregate(Min('total_score'))['total_score__min']
    return lowest_score

from django.db.models import Avg

def get_average_score(subject_id, session_id=None, term_id=None, branch_id=None):
    """
    Get the average score for a specific subject.

    :param subject_id: ID of the subject
    :param session_id: (Optional) ID of the session
    :param term_id: (Optional) ID of the term
    :param branch_id: (Optional) ID of the branch
    :return: The average score (rounded to 2 decimal places) or None if no results are found
    """
    filters = {'subject_id': subject_id}
    
    if session_id:
        filters['session_id'] = session_id
    if term_id:
        filters['term_id'] = term_id
    if branch_id:
        filters['branch_id'] = branch_id

    average_score = StudentFinalResult.objects.filter(**filters).aggregate(Avg('total_score'))['total_score__avg']
    
    if average_score is not None:
        return round(average_score, 2)
    return None

def get_student_average(student_id, session_id=None, term_id=None, branch_id=None):
    """
    Calculate a student's average score as a percentage.

    :param student_id: ID of the student
    :param session_id: (Optional) ID of the session
    :param term_id: (Optional) ID of the term
    :param branch_id: (Optional) ID of the branch
    :return: Average percentage score or None if no scores are found
    """
    filters = {'student_id': student_id}
    
    if session_id:
        filters['session_id'] = session_id
    if term_id:
        filters['term_id'] = term_id
    if branch_id:
        filters['branch_id'] = branch_id

    # Fetch total scores obtained by the student
    results = StudentFinalResult.objects.filter(**filters)
    total_obtained = results.aggregate(total_obtained=Sum('total_score'))['total_obtained']

    # Calculate maximum obtainable score
    total_subjects = results.count()
    max_obtainable = total_subjects * 100  # Assuming max score per subject is 100

    if total_obtained is not None and max_obtainable > 0:
        return round((total_obtained / max_obtainable) * 100, 2)  # Return percentage
    return None
