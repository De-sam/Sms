from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Staff, Role
from schools.models import Branch

class StaffCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=True)
    branches = forms.ModelMultipleChoiceField(queryset=Branch.objects.none(), required=True, widget=forms.CheckboxSelectMultiple)
    gender = forms.ChoiceField(choices=Staff.GENDER_CHOICES, required=True)
    marital_status = forms.ChoiceField(choices=Staff.MARITAL_STATUS_CHOICES, required=True)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)  # Updated to use a calendar-style date picker
    phone_number = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=True)  # Modified to 2 rows
    nationality = forms.ChoiceField(choices=Staff.NATIONALITY_CHOICES, required=True)
    staff_category = forms.ChoiceField(choices=Staff.STAFF_CATEGORY_CHOICES, required=True)
    cv = forms.FileField(required=False)
    profile_picture = forms.ImageField(required=False)
    staff_signature = forms.FileField(required=False)

    class Meta:
        model = User
        fields = [
            'username', 
            'first_name', 
            'last_name', 
            'email', 
            'password1', 
            'password2'    
        ]

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)  # Extract the school instance from kwargs
        super().__init__(*args, **kwargs)
        if school:
            self.fields['branches'].queryset = Branch.objects.filter(school=school)  # Filter branches by the specific school

    def save(self, commit=True, school=None):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            staff = Staff.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                gender=self.cleaned_data['gender'],
                marital_status=self.cleaned_data['marital_status'],
                date_of_birth=self.cleaned_data['date_of_birth'],
                phone_number=self.cleaned_data['phone_number'],
                address=self.cleaned_data['address'],
                nationality=self.cleaned_data['nationality'],
                staff_category=self.cleaned_data['staff_category'],
                cv=self.cleaned_data['cv'],
                profile_picture=self.cleaned_data['profile_picture'],
                staff_signature=self.cleaned_data['staff_signature'],
            )
            staff.branches.set(self.cleaned_data['branches'])  # Save the selected branches
            staff.save()  # Save the staff instance
        return user
