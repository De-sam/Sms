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
from django_select2.forms import Select2Widget
from django_select2.forms import ModelSelect2Widget
from academics.models import Session

class StudentCreationForm(forms.ModelForm):
    # Additional fields
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

    gender = forms.ChoiceField(choices=Student.GENDER_CHOICES, required=True)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    blood_group = forms.ChoiceField(choices=Student.BLOOD_GROUP_CHOICES, required=False)
    peculiar_illnesses = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    nationality = forms.ChoiceField(choices=Student.NATIONALITY_CHOICES, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=True)
    profile_picture = forms.ImageField(required=False)

    branch = forms.ModelChoiceField(queryset=Branch.objects.none(), required=True, label="Branch")
    admission_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    last_admitted_class = forms.CharField(max_length=100, required=True)
    student_class = forms.ModelChoiceField(queryset=Class.objects.none(), required=True)

    status = forms.ChoiceField(choices=Student.STATUS_CHOICES, required=True)

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'email', 'gender', 'date_of_birth', 'branch',
            'student_class', 'status', 'profile_picture', 'blood_group',
            'peculiar_illnesses', 'nationality', 'address', 'admission_date', 'last_admitted_class'
        ]

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        # Populate email from User instance if editing
        if self.instance.pk and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

        # Set branch queryset based on school
        if school:
            self.fields['branch'].queryset = Branch.objects.filter(school=school)
        else:
            self.fields['branch'].queryset = Branch.objects.none()

        # Pre-fill student_class queryset based on branch if editing
        if self.instance.pk and self.instance.branch:
            self.fields['student_class'].queryset = Class.objects.filter(branches=self.instance.branch)
            self.fields['student_class'].initial = self.instance.student_class

        # Dynamically load classes based on selected branch during form submission
        if 'branch' in self.data:
            try:
                branch_id = int(self.data.get('branch'))
                self.fields['student_class'].queryset = Class.objects.filter(branches__id=branch_id)
            except (ValueError, TypeError):
                self.fields['student_class'].queryset = Class.objects.none()

    def save(self, commit=True):
        # Determine if this is a new student record
        new_record = self.instance.pk is None
        
        # Handle user instance for Student
        email = self.cleaned_data['email']
        
        # Check if editing an existing student with a linked user
        if self.instance.pk and self.instance.user:
            user = self.instance.user
        else:
            # Create a new User instance
            user = User(email=email)
            user.set_password("student")  # Set a default password for the student

        # Update or set the user's email
        user.email = email
        user.save()  # Save user to assign a user ID if new

        # Link user to the student instance
        self.instance.user = user
        student = super().save(commit=False)
        student.branch = self.cleaned_data['branch']
        student.student_class = self.cleaned_data['student_class']

        # Automatically assign the current session
        school = self.cleaned_data['branch'].school  # Assuming branch is linked to a school
        current_session = Session.objects.filter(school=school, is_active=True).first()
        if current_session:
            student.current_session = current_session

        # Commit to save the student record and generate a unique ID if new
        if commit:
            student.save()

        # Generate username if not set (e.g., for new users)
        if not user.username:
            last_initial = self.cleaned_data['last_name'][0].upper()
            first_name = self.cleaned_data['first_name'].capitalize()
            student_id = student.id
            user.username = f"{last_initial}{first_name}-{student_id}"
            user.save()

        # Only send the creation email if it's a new student record
        if new_record:
            school_shortcode = getattr(student.branch.school, 'short_code', None)
            if school_shortcode:
                send_student_creation_email.delay(
                    user.email,
                    user.username,
                    school_shortcode,
                    self.cleaned_data['first_name'],
                    self.cleaned_data['last_name']
                )
            else:
                print("Error: School short_code not found while sending email.")

        return student



class ParentGuardianCreationForm(forms.ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = ParentGuardian
        fields = ['title', 'first_name', 'last_name', 'phone_number', 'email', 'address']
        labels = {'last_name': 'Surname'}

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)  # Extract school if passed
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Exclude the current user's email from the uniqueness check
            if self.instance.pk:  # Check if this is an edit
                if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
                    raise forms.ValidationError("A user with this email already exists.")
            else:  # For new records
                if User.objects.filter(email=email).exists():
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
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        email = self.cleaned_data['email']

        # Check if this is a new record or an edit
        is_new = self.instance.pk is None

        # Generate or update the User instance
        if is_new:
            username = self.generate_unique_username(first_name, last_name)
            user = User(username=username, email=email)
            user.set_password("parent")  # Set a default password for new users
        else:
            user = self.instance.user  # Get the associated User for existing ParentGuardian
            user.email = email  # Update the user's email if it's an edit

        # Save the User instance
        user.save()

        # Link the user and save the ParentGuardian instance
        parent = super().save(commit=False)
        parent.user = user

        # Link the parent to the school if provided
        if self.school:
            parent.school = self.school

        if commit:
            parent.save()

            # Send creation email only for new parents
            if is_new:
                short_code = self.school.short_code if self.school else 'default'
                send_parent_creation_email.delay(
                    email=email,
                    username=user.username,
                    short_code=short_code,
                    first_name=first_name,
                    last_name=last_name
                )

        return parent


class ParentGuardianWidget(ModelSelect2Widget):
    model = ParentGuardian
    search_fields = [
        'title__icontains',
        'first_name__icontains',
        'last_name__icontains',
    ]
    # Optionally, set a queryset limit
    queryset = ParentGuardian.objects.all()

    def label_from_instance(self, obj):
        title_display = f"{obj.get_title_display()} " if obj.title else ""
        return f"{title_display}{obj.first_name} {obj.last_name}"


class ParentAssignmentForm(forms.Form):
    parent = forms.ModelChoiceField(
        queryset=ParentGuardian.objects.none(),  # Default to no queryset
        widget=forms.Select(attrs={'class': 'form-control', 'data-placeholder': 'Search for a parent...'}),
        required=False,
        label="Select Parent"
    )

    relation_type = forms.ChoiceField(
        choices=ParentStudentRelationship.RELATION_TYPE_CHOICES,
        required=False,
        label="Relation Type"
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)  # Extract school context
        super().__init__(*args, **kwargs)

        if school:
            # Filter parents linked to the given school
            self.fields['parent'].queryset = ParentGuardian.objects.filter(school=school)


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