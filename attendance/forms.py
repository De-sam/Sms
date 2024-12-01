from django import forms
from academics.models import Session, Term
from schools.models import Branch
from .models import SchoolDaysOpen

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

