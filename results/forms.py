from django import forms
from .models import ResultStructure, ResultComponent
from classes.models import Class


class ResultStructureForm(forms.ModelForm):
    """
    Form for creating or updating a result structure.
    Allows users to define CA and Exam totals for the structure.
    """

    class Meta:
        model = ResultStructure
        fields = ['session', 'term', 'branch', 'classes', 'ca_total', 'exam_total', 'conversion_total']

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)  # Expect `school` to be passed during initialization
        super().__init__(*args, **kwargs)

        if school:
            # Dynamically filter sessions, terms, and branches based on the school
            self.fields['session'].queryset = school.session_set.all()
            self.fields['term'].queryset = school.term_set.none()  # Populate via AJAX
            self.fields['branch'].queryset = school.branch_set.all()
            self.fields['classes'].queryset = Class.objects.none()  # Initially empty

        # Add custom attributes for dynamic interactions
        self.fields['classes'].widget.attrs.update({'class': 'form-check-input'})

class ResultComponentForm(forms.ModelForm):
    """
    Form for creating or updating components of a result structure.
    Each component has a name and the maximum marks allocated to it.
    """

    class Meta:
        model = ResultComponent
        fields = ['name', 'max_marks']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Component Name'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Maximum Marks'}),
        }

    def clean_maximum_marks(self):
        """
        Ensure maximum marks is a positive value.
        """
        maximum_marks = self.cleaned_data.get('maximum_marks')
        if maximum_marks <= 0:
            raise forms.ValidationError("Maximum marks must be a positive value.")
        return maximum_marks
