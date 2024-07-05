from django.shortcuts import render

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
    pass

def features(request):
    pass

def pricing(request):
    pass

def registration(request):
    pass






