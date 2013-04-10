import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
from trees.models import Scenario
from trees.utils import create_scenariostands

scenario1 = Scenario.objects.get(name="My Scenario")

print "Creating identity"
import time
x = time.time()
scenariostands = create_scenariostands(scenario1)
print time.time() - x
print "%d scenariostands created" % scenariostands.count()
