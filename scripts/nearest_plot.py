import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
from trees.utils import nearest_plot
try:
    print nearest_plot(cancov=float(sys.argv[1]), stndhgt=float(sys.argv[2]))
except IndexError:
    print "Need to specify:\n   1. canopy cover (%)\n   2. stand height (m)"
