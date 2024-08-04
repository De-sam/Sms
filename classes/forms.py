from django import forms
from schools.models import Branch
from .models import Class

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

    class Meta:
        model = Class
        fields = ['name', 'department', 'arms']
        
    def __init__(self, *args, **kwargs):
        branches_queryset = kwargs.pop('branches_queryset', Branch.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['branches'].queryset = branches_queryset