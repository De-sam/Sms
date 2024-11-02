from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ClassAssignmentForm,ClassCreationForm,SubjectForm
from django.core.paginator import Paginator
from schools.models import Branch, PrimarySchool
from landingpage.models import SchoolRegistration
from classes.models import Class,Subject
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
        return redirect('primary_school_classes', short_code=short_code)

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
        return redirect('secondary_school_classes', short_code=short_code)

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
            return redirect('add_class_primary', short_code=short_code)
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
    # Get the school associated with the short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    try:
        # Attempt to get the PrimarySchool instance
        primary_school = PrimarySchool.objects.get(parent_school=school)
    except PrimarySchool.DoesNotExist:
        primary_school = []

    # Fetch only the primary school branches associated with this specific school
    primary_school_branches = Branch.objects.filter(school=school, primary_school__isnull=False)

    # Get the selected branch from GET parameters, if any
    selected_branch_id = request.GET.get('branch')
    if selected_branch_id:
        # Ensure the selected branch belongs to the current school
        selected_branch = get_object_or_404(Branch, id=selected_branch_id, school=school, primary_school__isnull=False)
        primary_school_classes = Class.objects.filter(branches=selected_branch)
    else:
        primary_school_classes = Class.objects.filter(branches__in=primary_school_branches).distinct()

    # Create a list of (class, branch) pairs based on the current school
    class_branch_pairs = []
    for cls in primary_school_classes:
        for branch in primary_school_branches:  # Loop over branches for the current school only
            if branch in cls.branches.all() and (not selected_branch_id or branch.id == int(selected_branch_id)):
                class_branch_pairs.append((cls, branch))

    # Pagination
    paginator = Paginator(class_branch_pairs, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'school': school,
        'pry_school':primary_school,
        'branches': primary_school_branches,
        'class_branch_pairs': page_obj,  # Pass the paginated class-branch pairs
        'selected_branch_id': selected_branch_id,
        'paginator': paginator,
        'page_obj': page_obj,
    }
    
    return render(request, 'classes/primary_school_classes.html', context)

@login_required_with_short_code
def secondary_school_classes(request, short_code):
    # Get the school associated with the short_code
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    
    # Fetch only the secondary school branches associated with this specific school
    secondary_school_branches = Branch.objects.filter(school=school).exclude(primary_school__isnull=False)

    # Get the selected branch from GET parameters, if any
    selected_branch_id = request.GET.get('branch')
    if selected_branch_id:
        # Ensure the selected branch belongs to the current school
        selected_branch = get_object_or_404(Branch, id=selected_branch_id, school=school)
        secondary_school_classes = Class.objects.filter(branches=selected_branch)
    else:
        secondary_school_classes = Class.objects.filter(branches__in=secondary_school_branches).distinct()

    # Create a list of (class, branch) pairs based on the current school
    class_branch_pairs = []
    for cls in secondary_school_classes:
        for branch in secondary_school_branches:  # Loop over branches for the current school only
            if branch in cls.branches.all() and (not selected_branch_id or branch.id == int(selected_branch_id)):
                class_branch_pairs.append((cls, branch))

    # Pagination
    paginator = Paginator(class_branch_pairs, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'school': school,
        'branches': secondary_school_branches,
        'class_branch_pairs': page_obj,  # Pass the paginated class-branch pairs
        'selected_branch_id': selected_branch_id,
        'paginator': paginator,
        'page_obj': page_obj,
    }
    
    return render(request, 'classes/secondary_school_classes.html', context)

from django.core.paginator import Paginator

@login_required_with_short_code
def sec_subjects_by_branch(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school).exclude(primary_school__isnull=False)

    # Get the selected branch from GET parameters, if any
    selected_branch_id = request.GET.get('branch')
    if selected_branch_id:
        selected_branch = get_object_or_404(Branch, id=selected_branch_id, school=school)
        classes_in_branches = Class.objects.filter(branches=selected_branch).distinct()
    else:
        classes_in_branches = Class.objects.filter(branches__in=branches).distinct()

    # Get all subjects linked to the classes in these branches, ordered by name
    subjects_in_branches = Subject.objects.filter(classes__in=classes_in_branches).distinct().order_by('name')

    # Create a list of (subject, class) pairs
    subject_class_pairs = []
    for subject in subjects_in_branches:
        for cls in subject.classes.all():
            if not selected_branch_id or cls.branches.filter(id=selected_branch_id).exists():
                subject_class_pairs.append((subject, cls))

    # Implement pagination
    paginator = Paginator(subject_class_pairs, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'school': school,
        'branches': branches,
        'selected_branch_id': selected_branch_id,
        'page_obj': page_obj,  # Pass the paginated subject-class pairs
    }

    return render(request, 'classes/subjects_by_branch.html', context)

@login_required_with_short_code
def pry_subjects_by_branch(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    primary_school = get_object_or_404(PrimarySchool, parent_school=school)
    branches = Branch.objects.filter(primary_school__parent_school=school)

    # Get the selected branch from GET parameters, if any
    selected_branch_id = request.GET.get('branch')
    if selected_branch_id:
        selected_branch = get_object_or_404(Branch, id=selected_branch_id, primary_school=primary_school)
        classes_in_branches = Class.objects.filter(branches=selected_branch).distinct()
    else:
        classes_in_branches = Class.objects.filter(branches__in=branches).distinct()

    # Get all subjects linked to the classes in these branches, ordered by name
    subjects_in_branches = Subject.objects.filter(classes__in=classes_in_branches).distinct().order_by('name')

    # Create a list of (subject, class) pairs
    subject_class_pairs = []
    for subject in subjects_in_branches:
        for cls in subject.classes.all():
            if not selected_branch_id or cls.branches.filter(id=selected_branch_id).exists():
                subject_class_pairs.append((subject, cls))

    # Implement pagination
    paginator = Paginator(subject_class_pairs, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'school': school,
        'branches': branches,
        'pry_school': primary_school,
        'selected_branch_id': selected_branch_id,
        'page_obj': page_obj,  # Pass the paginated subject-class pairs
    }

    return render(request, 'classes/subjects_by_branch.html', context)
@login_required_with_short_code
def add_subject_pry(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)
    print(branches)
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject created and assigned to classes successfully!')
            return redirect('pry_subjects_by_branch', short_code=short_code)
    else:
        form = SubjectForm()
    
    return render(request, 'classes/add_subject.html', {'form': form, 'school': school, 'branch': branches})

@login_required_with_short_code
def add_subject_sec(request, short_code):
    school = get_object_or_404(SchoolRegistration, short_code=short_code)
    branches = Branch.objects.filter(school=school)
    print(branches)
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject created and assigned to classes successfully!')
            return redirect('sec_subjects_by_branch', short_code=short_code)
    else:
        form = SubjectForm()
    
    return render(request, 'classes/add_subject.html', {'form': form, 'school': school, 'branch': branches})