from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.forms import modelformset_factory
from django.core.paginator import Paginator
from .models import ResultStructure, ResultComponent
from .forms import ResultStructureForm, ResultComponentForm
from landingpage.models import SchoolRegistration
from utils.decorator import login_required_with_short_code
from utils.permissions import admin_required
from utils.context_helpers import get_user_roles
from classes.models import Subject
def create_result_structure(request, short_code):
    """
    View to create or update a result structure for a school branch.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    user_roles = get_user_roles(request.user, school)

    if request.method == 'POST':
        form = ResultStructureForm(request.POST, school=school)

        # Debugging: Print the term queryset
        print(f"DEBUG: Term queryset during POST: {form.fields['term'].queryset}")

        if form.is_valid():
            result_structure = form.save(commit=False)
            result_structure.save()
            form.save_m2m()  # Save the many-to-many field for classes
            messages.success(request, "Result structure created/updated successfully!")
            return redirect('create_result_structure', short_code=short_code)
        else:
            print(f"DEBUG: Form errors: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResultStructureForm(school=school)
        print(f"DEBUG: Term queryset during GET: {form.fields['term'].queryset}")

    return render(request, 'results/create_result_structure.html', {
        'form': form,
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
    branch = result_structure.branch  # Get the branch associated with the structure
    school = branch.school  # Get the school from the branch
    user_roles = get_user_roles(request.user, school)

    # Ensure the result structure belongs to the correct school
    if school.short_code != short_code:
        messages.error(request, "Invalid school or structure.")
        return redirect('list_result_structures', short_code=short_code)

    # Filter subjects based on the branch using related models
    subjects = Subject.objects.filter(classes__branches=branch).distinct()

    # Create a formset for managing components
    ComponentFormSet = modelformset_factory(
        ResultComponent,
        form=ResultComponentForm,
        extra=1,  # Allow adding new components
        can_delete=True  # Allow deleting components
    )

    if request.method == 'POST':
        formset = ComponentFormSet(request.POST, queryset=ResultComponent.objects.filter(structure=result_structure))

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
            print(f"DEBUG: Formset errors: {formset.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        formset = ComponentFormSet(queryset=ResultComponent.objects.filter(structure=result_structure))

    return render(request, 'results/add_result_components.html', {
        'formset': formset,
        'result_structure': result_structure,
        'school': school,
        'subjects': subjects,  # Pass subjects to the template
        **user_roles,
    })



@login_required_with_short_code
@admin_required
def list_result_structures(request, short_code):
    """
    View to list all result structures for a given school.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    result_structures = ResultStructure.objects.filter(branch__school=school).select_related('session', 'term', 'branch')
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
