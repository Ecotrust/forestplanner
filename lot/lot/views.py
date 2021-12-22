from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect

def lot_landing_page(request):
    '''
    Land Owner Tools: Pick Your Tool
    '''

    # get url
    domain = request.get_host().split(':')[0]
    # Check against DOMAIN_ROUTING
    if domain in settings.DOMAIN_ROUTING.keys() and settings.DOMAIN_ROUTING[domain]:
        # Redirect as appropriate
        redirect_key = settings.DOMAIN_ROUTING[domain]
        if redirect_key == 'landmapper':
            return redirect('/landmapper')
        if redirect_key == 'discovery':
            return redirect('/discovery')
        if redirect_key == 'forestplanner':
            return redirect('/map')

    return render(request, 'lot/common/lot_selection.html', {})

# account login page
def login(request):
    # TODO: write to handle wrong email address or password on login
    # if request.method == 'POST':
        # return django.contrib.auth.views.login()
    # else:
    context = {}
    # return render(request, 'discovery/account/login.html', context)
    return render(request, 'lot/account/login.html', context)
