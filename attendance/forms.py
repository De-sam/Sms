from django import forms
from academics.models import Session, Term
from schools.models import Branch
from .models import SchoolDaysOpen
from classes.models import Class
from .models import StudentAttendance


class SchoolDaysOpenForm(forms.ModelForm):
    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        label="Session",
        required=True
    )
    term = forms.ModelChoiceField(
        queryset=Term.objects.none(),  # Initially empty until a session is chosen
        label="Term",
        required=True
    )
    branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Branches",
        required=True,
        help_text="Select one or more branches"
    )
    days_open = forms.IntegerField(
        label="Number of Days School Opened",
        required=True,
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter number of days'})
    )

    class Meta:
        model = SchoolDaysOpen
        fields = ['session', 'term', 'branches', 'days_open']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['term'].queryset = Term.objects.none()

        if 'session' in self.data:
            try:
                session_id = int(self.data.get('session'))
                self.fields['term'].queryset = Term.objects.filter(session_id=session_id)
            except (ValueError, TypeError):
                pass  # If the session ID isn't valid, keep the queryset empty
        elif self.instance.pk:
            self.fields['term'].queryset = Term.objects.filter(session=self.instance.session)



class StudentAttendanceFilterForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        required=True,
        label="Session"
    )
    term = forms.ModelChoiceField(
        queryset=Term.objects.none(),  # To be populated dynamically based on selected session
        required=True,
        label="Term"
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.none(),  # To be populated dynamically based on the selected school
        required=True,
        label="Branch"
    )
    classes = forms.ModelMultipleChoiceField(
        queryset=Class.objects.none(),  # To be populated dynamically based on selected branch
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Class(es)"
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        
        if school:
            self.fields['session'].queryset = Session.objects.filter(school=school)
            self.fields['branch'].queryset = Branch.objects.filter(school=school)





class StudentAttendanceForm(forms.ModelForm):
    class Meta:
        model = StudentAttendance
        fields = ['student', 'attendance_count']
        widgets = {
            'student': forms.HiddenInput(),  # Hidden input because student is determined by the context
            'attendance_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['attendance_count'].label = "Number of Days Attended"
