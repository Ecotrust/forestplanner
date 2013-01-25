import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', '..', '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
from local_util import filter_stand_list 

if __name__ == "__main__":

        # This guy matches condition 1332 almost exactly
        stand_list = [
            # species, sizeclass, tpa
            ('Douglas-fir', 6, 160),
            ('Douglas-fir', 10, 31),
            ('Douglas-fir', 14, 7),
            ('Western hemlock', 14, 5),
            ('Western redcedar', 14, 5),
            #('Red alder', 6, 40),
        ]

        min_candidates = 1 
        max_tpa_factor = 10 # we tolerate, at most +/- x x tpa

        filter_stand_list(stand_list, min_candidates, max_tpa_factor)

