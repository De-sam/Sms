from django import forms
from academics.models import Session, Term
from schools.models import Branch
from classes.models import Class
from .models import Rating



class RatingFilterForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        required=True,
        label="Session",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    term = forms.ModelChoiceField(
        queryset=Term.objects.none(),  # Dynamically populated
        required=True,
        label="Term",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    rating_type = forms.ChoiceField(
        choices=[
            ('psychomotor', 'Psychomotor'),
            ('behavioral', 'Behavioral'),
        ],
        required=True,
        label="Rating Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.none(),  # Dynamically populated
        required=True,
        label="Branch",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    classes = forms.ModelMultipleChoiceField(
        queryset=Class.objects.none(),  # Dynamically populated
        required=True,
        label="Class(es)",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)  # Pass school dynamically
        super().__init__(*args, **kwargs)

        if school:
            self.fields['session'].queryset = Session.objects.filter(school=school)
            self.fields['branch'].queryset = Branch.objects.filter(school=school)





class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = [
            'coordination', 'handwriting', 'sports', 'artistry', 
            'verbal_fluency', 'games',  # Psychomotor fields
            'punctuality', 'attentiveness', 'obedience', 
            'leadership', 'emotional_stability', 'teamwork',  # Behavioral fields
        ]
        widgets = {
            'coordination': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'handwriting': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'sports': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'artistry': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'verbal_fluency': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'games': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'punctuality': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'attentiveness': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'obedience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'leadership': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'emotional_stability': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
            'teamwork': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
        }

    def __init__(self, *args, **kwargs):
        rating_type = kwargs.pop('rating_type', None)
        super().__init__(*args, **kwargs)

        # Show only relevant fields based on the rating type
        if rating_type == 'psychomotor':
            self.fields['punctuality'].widget = forms.HiddenInput()
            self.fields['attentiveness'].widget = forms.HiddenInput()
            self.fields['obedience'].widget = forms.HiddenInput()
            self.fields['leadership'].widget = forms.HiddenInput()
            self.fields['emotional_stability'].widget = forms.HiddenInput()
            self.fields['teamwork'].widget = forms.HiddenInput()
        elif rating_type == 'behavioral':
            self.fields['coordination'].widget = forms.HiddenInput()
            self.fields['handwriting'].widget = forms.HiddenInput()
            self.fields['sports'].widget = forms.HiddenInput()
            self.fields['artistry'].widget = forms.HiddenInput()
            self.fields['verbal_fluency'].widget = forms.HiddenInput()
            self.fields['games'].widget = forms.HiddenInput()
