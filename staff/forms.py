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
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    phone_number = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=True)
    nationality = forms.ChoiceField(choices=Staff.NATIONALITY_CHOICES, required=True)
    staff_category = forms.ChoiceField(choices=Staff.STAFF_CATEGORY_CHOICES, required=True)
    status = forms.ChoiceField(choices=Staff.STATUS_CHOICES, required=True)
    cv = forms.FileField(required=True)
    profile_picture = forms.ImageField(required=False)
    staff_signature = forms.FileField(required=True)

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
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        # If editing an existing user, make password fields optional
        if self.instance and self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].help_text = "Leave blank if you don't want to change the password."
            self.fields['password2'].help_text = "Leave blank if you don't want to change the password."

        if school:
            self.fields['branches'].queryset = Branch.objects.filter(school=school)

        if self.instance and hasattr(self.instance, 'staff'):
            staff_instance = self.instance.staff
            self.fields['role'].initial = staff_instance.role
            self.fields['branches'].initial = staff_instance.branches.all()
            self.fields['gender'].initial = staff_instance.gender
            self.fields['marital_status'].initial = staff_instance.marital_status
            self.fields['date_of_birth'].initial = staff_instance.date_of_birth
            self.fields['phone_number'].initial = staff_instance.phone_number
            self.fields['address'].initial = staff_instance.address
            self.fields['nationality'].initial = staff_instance.nationality
            self.fields['staff_category'].initial = staff_instance.staff_category
            self.fields['status'].initial = staff_instance.status
            self.fields['cv'].initial = staff_instance.cv
            self.fields['profile_picture'].initial = staff_instance.profile_picture
            self.fields['staff_signature'].initial = staff_instance.staff_signature

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        # Only update the password if provided
        if self.cleaned_data['password1']:
            user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

            staff, created = Staff.objects.update_or_create(
                user=user,
                defaults={
                    'role': self.cleaned_data['role'],
                    'gender': self.cleaned_data['gender'],
                    'marital_status': self.cleaned_data['marital_status'],
                    'date_of_birth': self.cleaned_data['date_of_birth'],
                    'phone_number': self.cleaned_data['phone_number'],
                    'address': self.cleaned_data['address'],
                    'nationality': self.cleaned_data['nationality'],
                    'staff_category': self.cleaned_data['staff_category'],
                    'status': self.cleaned_data['status'],
                    'cv': self.cleaned_data.get('cv'),
                    'profile_picture': self.cleaned_data.get('profile_picture'),
                    'staff_signature': self.cleaned_data.get('staff_signature'),
                }
            )

            staff.branches.set(self.cleaned_data['branches'])
            staff.save()

        return user

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=True)
    branches = forms.ModelMultipleChoiceField(queryset=Branch.objects.none(), required=True, widget=forms.CheckboxSelectMultiple)
    gender = forms.ChoiceField(choices=Staff.GENDER_CHOICES, required=True)
    marital_status = forms.ChoiceField(choices=Staff.MARITAL_STATUS_CHOICES, required=True)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    phone_number = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=True)
    nationality = forms.ChoiceField(choices=Staff.NATIONALITY_CHOICES, required=True)
    staff_category = forms.ChoiceField(choices=Staff.STAFF_CATEGORY_CHOICES, required=True)
    status = forms.ChoiceField(choices=Staff.STATUS_CHOICES, required=True)
    cv = forms.FileField(required=False)
    profile_picture = forms.ImageField(required=False)
    staff_signature = forms.FileField(required=False)

    class Meta:
        model = User
        fields = [ 
            'first_name', 
            'last_name', 
            'email'
        ]

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields['branches'].queryset = Branch.objects.filter(school=school)

        if self.instance and hasattr(self.instance, 'staff'):
            staff_instance = self.instance.staff
            self.fields['role'].initial = staff_instance.role
            self.fields['branches'].initial = staff_instance.branches.all()
            self.fields['gender'].initial = staff_instance.gender
            self.fields['marital_status'].initial = staff_instance.marital_status
            self.fields['date_of_birth'].initial = staff_instance.date_of_birth
            self.fields['phone_number'].initial = staff_instance.phone_number
            self.fields['address'].initial = staff_instance.address
            self.fields['nationality'].initial = staff_instance.nationality
            self.fields['staff_category'].initial = staff_instance.staff_category
            self.fields['status'].initial = staff_instance.status
            self.fields['cv'].initial = staff_instance.cv
            self.fields['profile_picture'].initial = staff_instance.profile_picture
            self.fields['staff_signature'].initial = staff_instance.staff_signature

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

            staff, created = Staff.objects.update_or_create(
                user=user,
                defaults={
                    'role': self.cleaned_data['role'],
                    'gender': self.cleaned_data['gender'],
                    'marital_status': self.cleaned_data['marital_status'],
                    'date_of_birth': self.cleaned_data['date_of_birth'],
                    'phone_number': self.cleaned_data['phone_number'],
                    'address': self.cleaned_data['address'],
                    'nationality': self.cleaned_data['nationality'],
                    'staff_category': self.cleaned_data['staff_category'],
                    'status': self.cleaned_data['status'],
                    'cv': self.cleaned_data.get('cv'),
                    'profile_picture': self.cleaned_data.get('profile_picture'),
                    'staff_signature': self.cleaned_data.get('staff_signature'),
                }
            )

            staff.branches.set(self.cleaned_data['branches'])
            staff.save()

        return user