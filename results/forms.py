from django import forms
from .models import ResultStructure, ResultComponent
from classes.models import Class
from academics.models import Session, Term
from schools.models import Branch

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
            # Filter sessions, branches, and classes based on the school
            self.fields['session'].queryset = school.sessions.all()
            self.fields['branch'].queryset = Branch.objects.filter(school=school)
            self.fields['classes'].queryset = Class.objects.none()  # Initially empty

        # Handle dynamic filtering of terms
        if 'session' in self.data:
            try:
                session_id = int(self.data.get('session'))
                self.fields['term'].queryset = Term.objects.filter(session_id=session_id)
            except (ValueError, TypeError):
                self.fields['term'].queryset = Term.objects.none()
        elif self.instance.pk:
            # If editing an instance, populate terms based on the instance's session
            self.fields['term'].queryset = Term.objects.filter(session=self.instance.session)

        # Dynamically populate classes based on selected branch
        if 'branch' in self.data:
            try:
                branch_id = int(self.data.get('branch'))
                self.fields['classes'].queryset = Class.objects.filter(branches__id=branch_id)
            except (ValueError, TypeError):
                self.fields['classes'].queryset = Class.objects.none()

    def clean(self):
        """
        Perform additional validation for CA, Exam totals, and their conversion.
        """
        cleaned_data = super().clean()

        ca_total = cleaned_data.get('ca_total')
        exam_total = cleaned_data.get('exam_total')
        conversion_total = cleaned_data.get('conversion_total')

        if ca_total is not None and exam_total is not None:
            # Ensure CA and Exam totals sum to 100
            if ca_total + exam_total != 100:
                raise forms.ValidationError(
                    "The total of CA and Exam marks must equal 100."
                )

            # Ensure conversion total does not exceed the CA total
            if conversion_total and conversion_total > ca_total:
                raise forms.ValidationError(
                    "Conversion total cannot exceed the CA total."
                )

        return cleaned_data


class ResultComponentForm(forms.ModelForm):
    """
    Form for creating or updating components of a result structure.
    Each component has a name and the maximum marks allocated to it.
    """

    class Meta:
        model = ResultComponent
        fields = ['name', 'max_marks', 'subject']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Component Name'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Maximum Marks'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),  # Add dropdown for subjects
        }

    def clean_max_marks(self):
        """
        Ensure maximum marks is a positive value.
        """
        max_marks = self.cleaned_data.get('max_marks')
        if max_marks is not None and max_marks <= 0:
            raise forms.ValidationError("Maximum marks must be a positive value.")
        return max_marks
