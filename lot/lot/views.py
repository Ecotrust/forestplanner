from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

def lot_landing_page(request):
    '''
    Land Owner Tools: Pick Your Tool
    '''
    return render(request, 'lot/common/lot_selection.html', {})
