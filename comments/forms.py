from django import forms
from students.models import Student
from academics.models import Session, Term
from schools.models import Branch
from classes.models import Class
from .models import Comment

class CommentFilterForm(forms.Form):
    """
    Form for filtering students based on session, term, branch, and class.
    """
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
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields['session'].queryset = Session.objects.filter(school=school)
            self.fields['branch'].queryset = Branch.objects.filter(school=school)


class CommentForm(forms.ModelForm):
    """
    Form for adding comments for students.
    """
    class Meta:
        model = Comment
        fields = ['comment_text']
        widgets = {
            'comment_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter comment'}),
        }

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        session = kwargs.pop('session', None)
        term = kwargs.pop('term', None)
        author = kwargs.pop('author', None)
        super().__init__(*args, **kwargs)

        # Auto-set initial values for hidden fields
        self.fields['student'] = forms.ModelChoiceField(
            queryset=Student.objects.filter(id=student.id),
            initial=student,
            widget=forms.HiddenInput()
        )
        self.fields['session'] = forms.ModelChoiceField(
            queryset=Session.objects.filter(id=session.id),
            initial=session,
            widget=forms.HiddenInput()
        )
        self.fields['term'] = forms.ModelChoiceField(
            queryset=Term.objects.filter(id=term.id),
            initial=term,
            widget=forms.HiddenInput()
        )
        self.fields['author'] = forms.ModelChoiceField(
            queryset=Comment._meta.get_field('author').related_model.objects.filter(id=author.id),
            initial=author,
            widget=forms.HiddenInput()
        )
