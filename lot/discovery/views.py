from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def index(request):
    context = {}
    return render(request, 'discovery/common/base.html', context)

# landing page for non logged in users
def landing(request):
    context = {}
    return render(request, 'discovery/landing.html', context)

# account login page
def login(request):
    context = {}
    return render(request, 'discovery/account/login.html', context)

# account register page
def login(request):
    context = {}
    return render(request, 'discovery/account/login.html', context)

# account password reset and username recovery page
def login(request):
    context = {}
    return render(request, 'discovery/account/login.html', context)

# overwrite static content in lot app about.html
def about(request):
    context = {}
    return render(request, 'discovery/common/about.html', context)

# overwrite satic content in lot app documenation
def documentation(request):
    context = {}
    return render(request, 'discovery/common/documentation.html', context)

# support new layout for user stand/properties profiles
def stand_profile(request):
    context = {}
    return render(request, 'discovery/stand_profile.html', context)
