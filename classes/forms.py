from django import forms
from schools.models import Branch
from .models import Subject, Class, SubjectType, Department,Arm

class ClassAssignmentForm(forms.Form):
    branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.none(),  # Will be updated in the view
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    classes = forms.ModelMultipleChoiceField(
        queryset=Class.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

class ClassCreationForm(forms.ModelForm):
    assign_to_all = forms.BooleanField(required=False, label='Assign to All Branches')
    branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Select Branches'
    )
    arms = forms.ModelMultipleChoiceField(
        queryset=Arm.objects.all(),  # QuerySet to retrieve all Arm instances
        required=False,
        widget=forms.CheckboxSelectMultiple,  # Use CheckboxSelectMultiple for checkboxes
        label='Select Arms'
    )

    class Meta:
        model = Class
        fields = ['name', 'department', 'level', 'arms']
        
    def __init__(self, *args, **kwargs):
        branches_queryset = kwargs.pop('branches_queryset', Branch.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['branches'].queryset = branches_queryset

class SubjectForm(forms.ModelForm):
    classes = forms.ModelMultipleChoiceField(queryset=Class.objects.all(), widget=forms.CheckboxSelectMultiple)
    departments = forms.ModelMultipleChoiceField(queryset=Department.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = Subject
        fields = ['name', 'description', 'subject_type', 'departments', 'classes'] 
        widgets = {
            'description': forms.Textarea(attrs={'rows': 1, 'cols': 50}),  # Adjust rows and cols to reduce size
        }      