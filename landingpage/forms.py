# forms.py

from django import forms
from .models import SchoolRegistration
from .utilities import get_all_nigerian_states, get_local_governments

class SchoolRegistrationForm(forms.ModelForm):
    state_choices = [(state, state) for state in get_all_nigerian_states()]
    
    state = forms.ChoiceField(choices=state_choices)
    lga = forms.ChoiceField(choices=[])

    theme_primary_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}))
    theme_secondary_color = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}))

    class Meta:
        model = SchoolRegistration
        fields = [
            'school_name', 'address', 'city', 'state', 'lga', 'logo',
            'theme_primary_color', 'theme_secondary_color', 'admin_first_name',
            'admin_last_name', 'admin_email', 'admin_phone_number', 'referral_source'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'state' in self.data:
            state = self.data.get('state')
            self.fields['lga'].choices = [(lg, lg) for lg in get_local_governments().get(state, [])]
        else:
            self.fields['lga'].choices = []