from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.forms import modelformset_factory

from .models import ResultStructure, ResultComponent
from .forms import ResultStructureForm, ResultComponentForm  # Forms for creating/updating ResultStructure and ResultComponent
from landingpage.models import SchoolRegistration
from utils.decorator import login_required_with_short_code
from utils.permissions import admin_required


@login_required_with_short_code
@admin_required
@transaction.atomic
def create_result_structure(request, short_code):
    """
    View to create or update a result structure for a school branch.
    """
    school = get_object_or_404(SchoolRegistration, short_code=short_code)

    if request.method == 'POST':
        form = ResultStructureForm(request.POST, school=school)
        if form.is_valid():
            result_structure = form.save(commit=False)
            result_structure.school = school
            result_structure.save()
            messages.success(request, "Result structure created/updated successfully!")
            return redirect('create_result_structure', short_code=short_code)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResultStructureForm(school=school)

    return render(request, 'results/create_result_structure.html', {
        'form': form,
        'school': school,
    })


@login_required_with_short_code
@admin_required
@transaction.atomic
def add_result_components(request, short_code, structure_id):
    """
    View to add or update result components for a specific result structure.
    """
    result_structure = get_object_or_404(ResultStructure, id=structure_id)
    school = result_structure.school

    # Ensure the result structure belongs to the school in the request
    if school.short_code != short_code:
        messages.error(request, "Invalid school or structure.")
        return redirect('create_result_structure', short_code=short_code)

    # Create a formset for managing components
    ComponentFormSet = modelformset_factory(
        ResultComponent,
        form=ResultComponentForm,
        extra=1,  # Allow adding new components
        can_delete=True  # Allow deleting components
    )

    if request.method == 'POST':
        formset = ComponentFormSet(request.POST, queryset=ResultComponent.objects.filter(result_structure=result_structure))

        if formset.is_valid():
            components = formset.save(commit=False)
            for component in components:
                component.result_structure = result_structure
                component.save()

            # Delete removed components
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "Result components updated successfully!")
            return redirect('add_result_components', short_code=short_code, structure_id=structure_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        formset = ComponentFormSet(queryset=ResultComponent.objects.filter(result_structure=result_structure))

    return render(request, 'results/add_result_components.html', {
        'formset': formset,
        'result_structure': result_structure,
        'school': school,
    })
