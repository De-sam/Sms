from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import SchoolRegistration
from .utilities import get_all_nigerian_states, get_local_governments
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django.contrib.auth.models import User

class SchoolRegistrationForm(UserCreationForm):
    state_choices = [(state, state) for state in get_all_nigerian_states()]

    school_name = forms.CharField(max_length=255,widget=forms.Textarea(
        attrs={"placeholder":"Enter your school name",
               "rows":1,
    }), required=True)
    address = forms.CharField(widget=forms.Textarea(
        attrs={"rows":1,
               "placeholder":"Enter the address of your school"
    }), required=True)
    city = forms.CharField(max_length=100, required=True)
    state = forms.ChoiceField(choices=state_choices, error_messages={'required': 'State is required.'})
    lga = forms.ChoiceField(choices=[], error_messages={'required': 'LGA is required.'})
    logo = forms.ImageField(required=False)
    theme_color1 = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), error_messages={'required': 'Primary theme color is required.'})
    theme_color2 = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), error_messages={'required': 'Secondary theme color is required.'})
    username = forms.CharField(max_length=100, widget=forms.Textarea(
        attrs={"rows":1,
               "placeholder":"Enter a unique username"
    }) ,required=True)
    first_name = forms.CharField(max_length=100, widget=forms.Textarea(
        attrs={"rows":1,
    }) ,required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    admin_phone_number = forms.CharField(max_length=15, required=True)
    referral_source = forms.ChoiceField(choices=SchoolRegistration.REFERRAL_SOURCES, required=True)

    class Meta:
        model = User
        fields = (
            'username',
            'school_name',
            'address',
            'state',
            'lga',
            'city',
            'logo',
            'theme_color1',
            'theme_color2', 
            'first_name', 
            'last_name', 
            'email',
            'admin_phone_number',
            'referral_source',
            'password1', 
            'password2',
        )
        error_messages = {
            'school_name': {
                'required': 'School name is required.',
            },
            'address': {
                'required': 'Address is required.',
            },
            'city': {
                'required': 'City is required.',
            },
            'email': {
                'required': 'Admin email is required.',
                'unique': 'A school with this admin email already exists.',
            },
            'admin_phone_number': {
                'required': 'Admin phone number is required.',
            },
            'logo': {
                'required': 'School logo is required.',
            },
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            school = SchoolRegistration.objects.create(
                school_name=self.cleaned_data['school_name'],
                address=self.cleaned_data['address'],
                city=self.cleaned_data['city'],
                state=self.cleaned_data['state'],
                lga=self.cleaned_data['lga'],
                logo=self.cleaned_data.get('logo'),
                theme_color1=self.cleaned_data['theme_color1'],
                theme_color2=self.cleaned_data['theme_color2'],
                username=self.cleaned_data['username'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                admin_phone_number=self.cleaned_data['admin_phone_number'],
                referral_source=self.cleaned_data['referral_source'],
                admin_user=user
            )
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'state' in self.data:
            state = self.data.get('state')
            self.fields['lga'].choices = [(lg, lg) for lg in get_local_governments().get(state, [])]
        elif self.instance and self.instance.pk:
            state = self.instance.state
            self.fields['lga'].choices = [(lg, lg) for lg in get_local_governments().get(state, [])]
        else:
            self.fields['lga'].choices = []

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if self.errors.get(field_name):
                field.widget.attrs.update({'class': 'form-control is-invalid'})

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'username', 'email', 'school_name', 'address', 'city', 'state', 'lga',
            'logo', 'theme_color1', 'theme_color2',
            'admin_phone_number', 'referral_source',
            Submit('submit', 'Register', css_class='btn btn-primary')
        )
