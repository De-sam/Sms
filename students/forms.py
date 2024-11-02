from django import forms
from django.contrib.auth.models import User
from .models import Student, ParentGuardian, ParentStudentRelationship
from classes.models import Class
from schools.models import Branch
from .utils import generate_student_username
from .tasks import send_student_creation_email,send_parent_creation_email
from django import forms
from django.contrib.auth.models import User
from .models import Student
from classes.models import Class
from schools.models import Branch
from .utils import generate_student_username
from .tasks import send_student_creation_email

class StudentCreationForm(forms.ModelForm):
    # Basic user information
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter a valid email'}),
        required=True
    )

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
        required=True
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter your surname'}),
        required=True
    )

    # Additional student-specific fields
    gender = forms.ChoiceField(choices=Student.GENDER_CHOICES, required=True)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    blood_group = forms.ChoiceField(choices=Student.BLOOD_GROUP_CHOICES, required=False)
    peculiar_illnesses = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    nationality = forms.ChoiceField(choices=Student.NATIONALITY_CHOICES, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=True)
    profile_picture = forms.ImageField(required=False)

    # Academic details
    branch = forms.ModelChoiceField(queryset=Branch.objects.none(), required=True, label="Branch")
    admission_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    last_admitted_class = forms.CharField(max_length=100, required=True)
    student_class = forms.ModelChoiceField(queryset=Class.objects.none(), required=True)

    # Status tracking
    status = forms.ChoiceField(choices=Student.STATUS_CHOICES, required=True)

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'gender', 'date_of_birth', 
                  'branch', 'student_class', 'status', 'profile_picture']

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)  # School passed as context
        super().__init__(*args, **kwargs)

        # Update label for last_name to 'Surname'
        self.fields['last_name'].label = "Surname"

        # Set branch queryset based on school if provided
        if school:
            self.school = school
            self.fields['branch'].queryset = Branch.objects.filter(school=school)
        else:
            self.fields['branch'].queryset = Branch.objects.none()

        # Initially, no classes are selected
        self.fields['student_class'].queryset = Class.objects.none()

        # Dynamically load classes when a branch is selected
        if 'branch' in self.data:
            try:
                branch_id = int(self.data.get('branch'))
                self.fields['student_class'].queryset = Class.objects.filter(branches__id=branch_id)
            except (ValueError, TypeError):
                self.fields['student_class'].queryset = Class.objects.none()
        elif self.instance.pk and self.instance.student_class:
            self.fields['student_class'].queryset = Class.objects.filter(branch=self.instance.branch)

    def save(self, commit=True):
        # First, check if a user with this email already exists
        email = self.cleaned_data['email']
        user = User.objects.filter(email=email).first()

        if not user:
            # If user doesn't exist, create one
            user = User(
                username=email,  # Using email as username initially
                email=email,
            )
            # Set a default password for the student
            default_password = "student"
            user.set_password(default_password)

        # Save User if not already saved
        if commit:
            user.save()

        # Create or update the student object linked to the user
        student, created = Student.objects.update_or_create(
            user=user,
            defaults={
                'first_name': self.cleaned_data['first_name'],
                'last_name': self.cleaned_data['last_name'],
                'gender': self.cleaned_data['gender'],
                'date_of_birth': self.cleaned_data['date_of_birth'],
                'blood_group': self.cleaned_data['blood_group'],
                'peculiar_illnesses': self.cleaned_data['peculiar_illnesses'],
                'nationality': self.cleaned_data['nationality'],
                'address': self.cleaned_data['address'],
                'profile_picture': self.cleaned_data['profile_picture'],
                'admission_date': self.cleaned_data['admission_date'],
                'last_admitted_class': self.cleaned_data['last_admitted_class'],
                'student_class': self.cleaned_data['student_class'],
                'status': self.cleaned_data['status'],
                'branch': self.cleaned_data['branch'],  # Save the branch!
            }
        )

        # Generate the username for the student if it's newly created
        if created:
            student_id = student.id
            username = generate_student_username(self.cleaned_data['first_name'], self.cleaned_data['last_name'], student_id)
            user.username = username
            user.save()

        # Send the email using the Celery task
        school_shortcode = self.school.short_code if hasattr(self, 'school') else None
        send_student_creation_email.delay(
            user.email,
            user.username,
            school_shortcode,
            self.cleaned_data['first_name'],
            self.cleaned_data['last_name']
        )

        return student  # Return student instead of user to avoid confusion


class StudentUpdateForm(forms.ModelForm):
    # Update form for existing student details
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    # Additional student-specific fields
    gender = forms.ChoiceField(choices=Student.GENDER_CHOICES, required=True)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    blood_group = forms.ChoiceField(choices=Student.BLOOD_GROUP_CHOICES, required=False)
    peculiar_illnesses = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    nationality = forms.ChoiceField(choices=Student.NATIONALITY_CHOICES, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=True)
    profile_picture = forms.ImageField(required=False)

    # Academic details
    branch = forms.ModelChoiceField(queryset=Branch.objects.none(), required=True, label="Branch")
    admission_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    last_admitted_class = forms.CharField(max_length=100, required=True)
    student_class = forms.ModelChoiceField(queryset=Class.objects.none(), required=False)

    # Status tracking
    status = forms.ChoiceField(choices=Student.STATUS_CHOICES, required=True)

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'gender', 'date_of_birth', 
                  'branch', 'student_class', 'status', 'profile_picture', 'blood_group', 
                  'peculiar_illnesses', 'nationality', 'address', 'admission_date', 'last_admitted_class']

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        # Set branch queryset based on school if provided
        if school:
            self.school = school
            self.fields['branch'].queryset = Branch.objects.filter(school=school)
        else:
            self.fields['branch'].queryset = Branch.objects.none()

        # Initially, no classes are selected
        self.fields['student_class'].queryset = Class.objects.none()

        # Dynamically load classes when a branch is selected
        if 'branch' in self.data:
            try:
                branch_id = int(self.data.get('branch'))
                self.fields['student_class'].queryset = Class.objects.filter(branches__id=branch_id)
            except (ValueError, TypeError):
                self.fields['student_class'].queryset = Class.objects.none()
        elif self.instance.pk and self.instance.student_class:
            self.fields['student_class'].queryset = Class.objects.filter(branches=self.instance.branch)

    def save(self, commit=True):
        # Save the Student object
        student = super().save(commit=False)
        user = student.user  # Access the related User object

        # Update the User's email with the cleaned data from the form
        user.email = self.cleaned_data['email']

        if commit:
            user.save()  # Save User changes
            student.save()  # Save Student changes

        return student


class ParentGuardianCreationForm(forms.ModelForm):
    email = forms.EmailField(required=True, help_text="Required. Will be used for login.")

    class Meta:
        model = ParentGuardian
        fields = ['title', 'first_name', 'last_name', 'phone_number', 'email', 'address']
        labels = {'last_name': 'Surname'}

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)  # Extract school if passed
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must be numeric.")
        if len(phone_number) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits long.")
        return phone_number

    def generate_unique_username(self, first_name, last_name):
        base_username = f"{first_name.lower()}.{last_name.lower()}"
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

    def save(self, commit=True):
        print(f"School context in save: {self.school}")  # Debug line
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        email = self.cleaned_data['email']

        username = self.generate_unique_username(first_name, last_name)
        user = User(username=username, email=email)
        default_password = "parent"
        user.set_password(default_password)

        parent = super().save(commit=False)
        parent.user = user  # Link User to ParentGuardian

        if commit:
            user.save()
            parent.save()

            # Use the short_code from the school context if available
            short_code = self.school.short_code if self.school else 'default'
            print(short_code)
            send_parent_creation_email.delay(
                email=email,
                username=username,
                short_code=short_code,
                first_name=first_name,
                last_name=last_name
            )

        return parent

    
class ParentAssignmentForm(forms.Form):
    parent = forms.ModelChoiceField(
        queryset=ParentGuardian.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Select Parent"
    )

    relation_type = forms.ChoiceField(
        choices=ParentStudentRelationship.RELATION_TYPE_CHOICES,
        required=True,
        label="Relation Type"
    )

class ParentStudentRelationshipForm(forms.ModelForm):
    class Meta:
        model = ParentStudentRelationship
        fields = ['parent_guardian', 'relation_type']

class ParentStudentRelationshipUpdateForm(forms.ModelForm):
    class Meta:
        model = ParentStudentRelationship
        fields = ['parent_guardian', 'relation_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customizing the form fields if needed, e.g., setting custom labels or attributes
        self.fields['parent_guardian'].label = "Select Parent/Guardian"
        self.fields['relation_type'].label = "Relationship Type"