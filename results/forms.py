from django import forms
from .models import ResultStructure, ResultComponent
from classes.models import Class, Subject
from academics.models import Session, Term
from schools.models import Branch
from django.forms import formset_factory
from .models import GradingSystem


class ResultStructureForm(forms.ModelForm):
    """
    Form for creating or updating a result structure.
    Allows users to define CA and Exam totals for the structure.
    """

    class Meta:
        model = ResultStructure
        fields = ['branch', 'ca_total', 'exam_total', 'conversion_total']

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)  # Expect `school` to be passed during initialization
        super().__init__(*args, **kwargs)

        if school:
            # Filter branches based on the school
            self.fields['branch'].queryset = Branch.objects.filter(school=school)

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
    """

    class Meta:
        model = ResultComponent
        fields = ['id', 'name', 'max_marks', 'subject']  # Include 'id' explicitly
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Component Name'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Maximum Marks'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),  # Dropdown for subjects
        }

    def __init__(self, *args, **kwargs):
        branch = kwargs.pop('branch', None)  # Pass the branch dynamically
        super().__init__(*args, **kwargs)

        if branch:
            # Filter subjects by the given branch
            self.fields['subject'].queryset = Subject.objects.filter(classes__branches=branch).distinct()
        else:
            # Default to an empty queryset if no branch is provided
            self.fields['subject'].queryset = Subject.objects.none()

    def clean_max_marks(self):
        """
        Ensure maximum marks is a positive value.
        """
        max_marks = self.cleaned_data.get('max_marks')
        if max_marks is not None and max_marks <= 0:
            raise forms.ValidationError("Maximum marks must be a positive value.")
        return max_marks


class ScoreFilterForm(forms.Form):
    session = forms.ModelChoiceField(queryset=Session.objects.all(), required=True, label="Session")
    term = forms.ModelChoiceField(queryset=Term.objects.none(), required=True, label="Term")
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), required=True, label="Branch")
    subject = forms.ModelChoiceField(queryset=Subject.objects.none(), required=True, label="Subject")
    classes = forms.ModelMultipleChoiceField(
        queryset=Class.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Classes"
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields['session'].queryset = Session.objects.filter(school=school)
            self.fields['branch'].queryset = Branch.objects.filter(school=school)

        if 'session' in self.data:
            try:
                session_id = int(self.data.get('session'))
                self.fields['term'].queryset = Term.objects.filter(session_id=session_id)
            except (ValueError, TypeError):
                self.fields['term'].queryset = Term.objects.none()

        if 'branch' in self.data:
            try:
                branch_id = int(self.data.get('branch'))
                self.fields['subject'].queryset = Subject.objects.filter(classes__branches=branch_id).distinct()
                self.fields['classes'].queryset = Class.objects.filter(branches=branch_id).distinct()
            except (ValueError, TypeError):
                self.fields['subject'].queryset = Subject.objects.none()
                self.fields['classes'].queryset = Class.objects.none()


