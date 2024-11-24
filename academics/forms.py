from django import forms
from .models import Session, Term

# Form for Adding Sessions
class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['session_name', 'start_date']
        widgets = {
            'start_date': forms.SelectDateWidget(),
        }
        labels = {
            'session_name': 'Session Name (e.g., 2023/24)',
            'start_date': 'Start Date',
        }

# Form for Adding Terms
class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['term_name', 'session', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.SelectDateWidget(),
            'end_date': forms.SelectDateWidget(),
        }
        labels = {
            'term_name': 'Term Name',
            'session': 'Academic Session',
            'start_date': 'Start Date',
            'end_date': 'End Date',
        }
