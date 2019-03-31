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
def register(request):
    context = {}
    return render(request, 'discovery/account/register.html', context)

# account password reset and username recovery page
def reset(request):
    context = {}
    return render(request, 'discovery/account/reset.html', context)

# support new layout for user stand/properties profiles
def stand_profile(request):
    context = {
        # Todo: add username condition and value
        'username': 'username',
        'title': 'properties',
        # use button_text and button_action together
        'button_text': '+ Add a new property',
        'button_action': '',
    }
    return render(request, 'discovery/common/grid.html', context)

# account password reset and username recovery page
def stands(request):
    context = {
        # Todo: add username condition and value
        'username': 'username',
        'title': 'properties',
        # use button_text and button_action together
        'button_text': '+ Add a new property',
        'button_action': '',
    }
    return render(request, 'discovery/common/grid.html', context)

# find your forest page
def find_your_forest(request):
    context = {
        'title': 'Find Your Forest',
        'flatblock_slug': 'find-your-forest',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
        # specific for action buttons template
        'act_btn_one_text': 'Choose an existing property',
        'act_btn_one_action': '/discovery/stands/',
        'act_btn_two_text': 'Map your own property',
        'act_btn_two_action': '/discovery/map/',
    }
    return render(request, 'discovery/common/action_buttons.html', context)

# overwrite static content in lot app about.html
def map(request):
    context = {
        'title': 'Map your property',
        'flatblock_slug': 'map-your-property',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
    }
    return render(request, 'discovery/map.html', context)

# overwrite static content in lot app about.html
def about(request):
    context = {}
    return render(request, 'discovery/common/about.html', context)

# overwrite satic content in lot app documenation
def documentation(request):
    context = {}
    return render(request, 'discovery/common/documentation.html', context)
