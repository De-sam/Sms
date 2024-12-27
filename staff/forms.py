from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Staff, Role
from schools.models import Branch
from classes.models import Subject, Class, TeacherSubjectClassAssignment
from django import forms
import datetime
from .utils import generate_unique_username
from academics.models import Session, Term
from django.core.exceptions import ValidationError
from utils.banking import fetch_bank_codes, verify_account_details
import datetime



class StaffUploadForm(forms.Form):
    file = forms.FileField()

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

    # Account details fields
    bank_name = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={"class": "form-select searchable-bank"})
    )
    account_number = forms.CharField(max_length=20, required=False)
    account_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    password1 = forms.CharField(
        required=True,
        label="Password",
        widget=forms.TextInput(attrs={'class': 'text-danger'})
    )
    password2 = forms.CharField(
        required=True,
        label="Confirm Password",
        widget=forms.TextInput(attrs={'class': 'text-danger'})
    )

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

        if school:
            self.fields['branches'].queryset = Branch.objects.filter(school=school)

        # Populate bank_name choices dynamically
        bank_codes = fetch_bank_codes()
        self.fields['bank_name'].choices = [("", "Select a bank")] + [
            (code, name) for code, name in bank_codes.items()
        ]

        if not self.instance.pk:
            current_year = datetime.datetime.now().year
            school_initials = ''.join([word[0].upper() for word in school.school_name.split()])

            if self.data.get('last_name'):
                self.fields['username'].initial = generate_unique_username(self.data['last_name'], current_year)
            else:
                self.fields['username'].initial = f"{school_initials}/{current_year}/1"

            self.fields['password1'].initial = 'new_staff'
            self.fields['password2'].initial = 'new_staff'

        self.fields['username'].widget.attrs['readonly'] = True

        if self.instance and self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].help_text = "Leave blank if you don't want to change the password."
            self.fields['password2'].help_text = "Leave blank if you don't want to change the password."

    def clean(self):
        cleaned_data = super().clean()
        bank_code = cleaned_data.get("bank_name")
        account_number = cleaned_data.get("account_number")

        if bank_code and account_number:
            # Verify account details
            account_details = verify_account_details(account_number, bank_code)
            if not account_details or 'account_name' not in account_details:
                raise ValidationError("Unable to verify account details. Please check the bank and account number.")
            # Populate account name
            cleaned_data['account_name'] = account_details['account_name']

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

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
                    'bank_name': self.cleaned_data.get('bank_name'),
                    'account_number': self.cleaned_data.get('account_number'),
                    'account_name': self.cleaned_data.get('account_name'),
                }
            )

            staff.branches.set(self.cleaned_data['branches'])
            staff.save()

        return user
    
class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label="Username")
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

    # New fields for bank details
    bank_name = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={"class": "form-select searchable-bank"})
    )
    account_number = forms.CharField(max_length=20, required=False)
    account_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

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
            self.fields['bank_name'].initial = staff_instance.bank_name
            self.fields['account_number'].initial = staff_instance.account_number
            self.fields['account_name'].initial = staff_instance.account_name

        # Populate bank_name choices dynamically
        from utils.banking import fetch_bank_codes
        bank_codes = fetch_bank_codes()
        self.fields['bank_name'].choices = [("", "Select a bank")] + [
            (code, name) for code, name in bank_codes.items()
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['username']
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
                    'bank_name': self.cleaned_data.get('bank_name'),
                    'account_number': self.cleaned_data.get('account_number'),
                    'account_name': self.cleaned_data.get('account_name'),
                }
            )

            staff.branches.set(self.cleaned_data['branches'])
            staff.save()

        return user

    

class TeacherSubjectAssignmentForm(forms.Form):
    branch = forms.ModelChoiceField(queryset=Branch.objects.none())
    subject = forms.ModelChoiceField(queryset=Subject.objects.none())
    classes = forms.ModelMultipleChoiceField(queryset=Class.objects.none(), widget=forms.CheckboxSelectMultiple)
    session = forms.ModelChoiceField(queryset=Session.objects.none())
    term = forms.ModelChoiceField(queryset=Term.objects.none())

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        branch_id = kwargs.pop('branch_id', None)
        staff = kwargs.pop('staff', None)
        super().__init__(*args, **kwargs)

        if school and staff:
            # Filter branches to only those associated with the school and assigned to the staff
            self.fields['branch'].queryset = Branch.objects.filter(school=school, staff=staff).distinct()
            self.fields['session'].queryset = Session.objects.filter(school=school)  # Populate session based on school

        if branch_id:
            branch = Branch.objects.get(id=branch_id)
            classes_in_branch = branch.classes.all()
            self.fields['subject'].queryset = Subject.objects.filter(classes__in=classes_in_branch).distinct()
            self.fields['classes'].queryset = classes_in_branch

        if self.data.get('session'):
            session_id = self.data.get('session')
            self.fields['term'].queryset = Term.objects.filter(session_id=session_id)

        if self.data.get('subject'):
            subject_id = int(self.data.get('subject'))
            self.fields['classes'].queryset = self.fields['classes'].queryset.filter(subjects__id=subject_id)
