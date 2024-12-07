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
from .models import ResultComponent
from django.db.models import Q
from academics.models import Session, Term
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from classes.models import Class, Subject
from .models import ResultStructure, ResultComponent, StudentResult
import json


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

            # Debug: Print component names in the terminal
            for component in components:
                print(f"Component Name: {component.name}, Subject: {component.subject}")

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
                "conversion_total": result_structure.conversion_total,
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@csrf_exempt
@transaction.atomic
def save_student_scores(request, short_code):
    """
    Save scores for students based on the submitted data.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            session_id = data.get("session")
            term_id = data.get("term")
            scores = data.get("scores", [])

            # Validate input
            if not session_id or not term_id or not scores:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            session = get_object_or_404(Session, id=session_id, school=school)
            term = get_object_or_404(Term, id=term_id, session=session)

            # Process scores
            for score_data in scores:
                student_id = score_data.get("student_id")
                component_scores = score_data.get("components", [])
                converted_ca = score_data.get("converted_ca")
                exam_score = score_data.get("exam_score")

                student = get_object_or_404(Student, id=student_id, current_session=session)

                # Save individual component scores
                for component_score in component_scores:
                    component_id = component_score.get("component_id")
                    score = component_score.get("score")

                    component = get_object_or_404(ResultComponent, id=component_id)
                    StudentResult.objects.update_or_create(
                        student=student,
                        component=component,
                        defaults={"score": score}
                    )

                # Calculate and save the total score
                total_ca = sum(int(cs.get("score", 0)) for cs in component_scores)
                total_score = total_ca + int(exam_score or 0)
                StudentResult.objects.update_or_create(
                    student=student,
                    defaults={
                        "converted_ca": converted_ca,
                        "exam_score": exam_score,
                        "total_score": total_score
                    }
                )

            return JsonResponse({"success": True, "message": "Scores saved successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)
