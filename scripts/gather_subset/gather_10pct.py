import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################e
from trees.models import TreeliveSummary
from trees.plots import get_nearest_neighbors
from trees.models import ConditionVariantLookup
from trees.models import IdbSummary

fh = open("matches.csv", 'a')
fh.write(','.join(['original_condition', 'variant', 'matched_condition', 'certainty']))
fh.write('\n')

for cvl in list(ConditionVariantLookup.objects.filter(cond_id__gt=27136)):

    cond = cvl.cond_id
    variant = cvl.variant_code
    print
    print variant, cond

    tls = TreeliveSummary.objects.filter(cond_id=cond)
    stand_list = [tuple(tl.treelist) for tl in tls]

    idb = IdbSummary.objects.get(cond_id=cond)
    site_cond = {
        'calc_aspect': idb.calc_aspect,
        'elev_ft': idb.elev_ft,
        'latitude_fuzz': idb.latitude_fuzz,
        'longitude_fuzz': idb.longitude_fuzz,
        'calc_slope': idb.calc_slope,
        'stand_age': idb.stand_age
    }

    weight_dict = None

    try:
        ps, num_candidates = get_nearest_neighbors(
            site_cond, stand_list, variant, weight_dict, k=4)
    except:
        print "Error: ", site_cond
        continue

    if num_candidates < 2:
        print "DID NOT MATCH ANYTHING BUT ITSELF"
        continue

    for pseries in ps[1:4]:  # top 3
        # ['original_condition', 'variant', 'matched_condition', 'certainty']
        certainty = pseries['_certainty']
        if certainty < 0.75:  # ... that are at least 75% certain
            continue
        data = [cond, variant, pseries.name, certainty]
        fh.write(','.join([str(x) for x in data]))
        fh.write("\n")
        fh.flush()
