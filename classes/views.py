from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ClassAssignmentForm,ClassCreationForm
from schools.models import Branch, PrimarySchool
from landingpage.models import SchoolRegistration
from classes.models import Class
from schools.views import login_required_with_short_code


@login_required_with_short_code
def assign_classes_primary(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    primary_school = get_object_or_404(PrimarySchool, parent_school=school)
    primary_branches = Branch.objects.filter(primary_school=primary_school)
    
    form = ClassAssignmentForm(request.POST or None)
    form.fields['branches'].queryset = primary_branches

    if request.method == 'POST' and form.is_valid():
        selected_branches = form.cleaned_data['branches']
        selected_classes = form.cleaned_data['classes']
        for branch in selected_branches:
            branch.classes.set(selected_classes)  # This will overwrite previous assignments
        messages.success(request, 'Classes assigned to selected primary branches successfully!')
        return redirect('branch_list', short_code=short_code)

    return render(request, 'classes/assign_classes.html', {
        'form': form,
        'school': school,
        'pry_school': primary_school,
        'branch_type': 'Primary',
    })


@login_required_with_short_code
def assign_classes_secondary(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    secondary_branches = Branch.objects.filter(school=school).exclude(primary_school__isnull=False)
    
    form = ClassAssignmentForm(request.POST or None)
    form.fields['branches'].queryset = secondary_branches

    if request.method == 'POST' and form.is_valid():
        selected_branches = form.cleaned_data['branches']
        selected_classes = form.cleaned_data['classes']
        for branch in selected_branches:
            branch.classes.set(selected_classes)  # This will overwrite previous assignments
        messages.success(request, 'Classes assigned to selected secondary branches successfully!')
        return redirect('branch_list', short_code=short_code)

    return render(request, 'classes/assign_classes.html', {
        'form': form,
        'school': school,
        'branch_type': 'Secondary',
    })

@login_required_with_short_code
def add_class_primary(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    primary_branches = Branch.objects.filter(primary_school__parent_school=school)
    
    if request.method == 'POST':
        form = ClassCreationForm(request.POST, branches_queryset=primary_branches)
        if form.is_valid():
            assign_to_all = form.cleaned_data['assign_to_all']
            selected_branches = form.cleaned_data['branches']
            classes = form.save(commit=False)
            classes.save()
            
            if assign_to_all:
                # Assign class to all primary branches
                for branch in primary_branches:
                    branch.classes.add(classes)
            else:
                # Assign class to selected branches only
                for branch in selected_branches:
                    branch.classes.add(classes)
            
            messages.success(request, 'Class created successfully!')
            return redirect('primary_branch_list', short_code=short_code)
    else:
        form = ClassCreationForm(branches_queryset=primary_branches)
    
    return render(request, 'classes/add_class.html', {
        'form': form,
        'school': school,
        'primary_branches': primary_branches
    })


@login_required_with_short_code
def add_class_secondary(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    secondary_branches = Branch.objects.filter(school=school).exclude(primary_school__isnull=False)
    
    if request.method == 'POST':
        form = ClassCreationForm(request.POST, branches_queryset=secondary_branches)
        if form.is_valid():
            assign_to_all = form.cleaned_data['assign_to_all']
            selected_branches = form.cleaned_data['branches']
            classes = form.save(commit=False)
            classes.save()
            
            if assign_to_all:
                # Assign class to all secondary branches
                for branch in secondary_branches:
                    branch.classes.add(classes)
            else:
                for branch in selected_branches:
                    branch.classes.add(classes)
            
            messages.success(request, 'Class created successfully!')
            return redirect('add_class_secondary', short_code=short_code)
    else:
        form = ClassCreationForm(branches_queryset=secondary_branches)
    
    return render(request, 'classes/add_class.html', {
        'form': form,
        'school': school,
        'secondary_branches': secondary_branches
    })

@login_required_with_short_code
def primary_school_classes(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Fetch primary schools associated with the secondary school
    primary_schools = PrimarySchool.objects.filter(parent_school=school)
    
    # Fetch classes linked to primary schools
    primary_school_classes = Class.objects.filter(branches__primary_school__in=primary_schools)
    
    context = {
        'school': school,
        'primary_schools': primary_schools,
        'classes': primary_school_classes,
    }
    
    return render(request, 'classes/primary_school_classes.html', context)

@login_required_with_short_code
def secondary_school_classes(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Fetch branches associated with the secondary school
    secondary_school_branches = Branch.objects.filter(school=school).exclude(primary_school__isnull=False)
    
    # Fetch classes linked to secondary school branches
    secondary_school_classes = Class.objects.filter(branches__in=secondary_school_branches)
    
    context = {
        'school': school,
        'branches': secondary_school_branches,
        'classes': secondary_school_classes,
    }
    
    return render(request, 'classes/secondary_school_classes.html', context)

