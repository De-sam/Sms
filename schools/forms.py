from django import forms
from landingpage.models import SchoolRegistration
from .models import Branch , PrimarySchool

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

class SchoolProfileUpdateForm(forms.ModelForm):
    
    logo = forms.ImageField(required=False)
    theme_color1 = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), error_messages={'required': 'Primary theme color is required.'})
    theme_color2 = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), error_messages={'required': 'Secondary theme color is required.'})
    email = forms.EmailField(required=True)
    admin_phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = SchoolRegistration
        fields = (
            'school_name',
            'address',
            'logo',
            'theme_color1',
            'theme_color2', 
            'email',
            'admin_phone_number',
        )
        error_messages = {
            'school_name': {
                'required': 'School name is required.',
            },
            'address': {
                'required': 'Address is required.',
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


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['branch_name', 'address']



class PrimarySchoolForm(forms.ModelForm):
    class Meta:
        model = PrimarySchool
        fields = ['school_name', 'address', 'logo']

class UpdatePrimarySchoolForm(forms.ModelForm):
    class Meta:
        model = PrimarySchool
        fields = ['school_name', 'address', 'logo']


class PrimaryBranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['branch_name', 'address']      
        
        