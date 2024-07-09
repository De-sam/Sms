from django.shortcuts import render, redirect
from .forms import SchoolRegistrationForm
from django.contrib import messages
from .utilities import get_all_nigerian_states, get_local_governments, generate_shortcode


# Create your views here.
def home(request):
    return render(request,
            'landingpage/home.html',
            {'title':'Home'})

def about(request):
    return render(request,
            'landingpage/about.html',
            {'title':'About'})

def contact(request):
    return render(request,
            'landingpage/contact.html',
            {'title':'Contact'})

def features(request):
    return render(request,
            'landingpage/features.html',
            {'title':'Features'})

def pricing(request):
    return render(request,
            'landingpage/pricing.html',
            {'title':'Pricing'})

def generate_shortcode(name):
    words = name.split()
    shortcode = ''.join([word[0] + word[-1] for word in words]).lower()
    return shortcode

def registration(request):
    if request.method == 'POST':
        form = SchoolRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Generate the shortcode from the school name
            school_name = form.cleaned_data['school_name']
            shortcode = generate_shortcode(school_name)
            form.instance.short_code = shortcode

            form.save()
            messages.success(request, 'School registered successfully! An email will be sent to the administrator.')
            return redirect('landingpage:registration')
    else:
        form = SchoolRegistrationForm()

    if 'state' in request.GET:
        state = request.GET.get('state')
        local_governments = get_local_governments().get(state, [])
        form.fields['lga'].choices = [(lg, lg) for lg in local_governments]

    return render(request, 'landingpage/registration.html', {'title': 'Registration', 'form': form})




