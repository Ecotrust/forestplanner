import os, csv
# os.environ['DJANGO_SETTINGS_MODULE']='settings'
from django.conf import settings
from trees.models import *
from trees.plots import *
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def violation(self, msg):
        self.errors += 1
        print msg

    def handle(self, *args, **options):

        CANDIDATES_DESIRED = 10  # How many candidates would you like?
        MAX_ITERATIONS = 0      # <1 for 'run all'

        match_dicts = []
        miss_count = 0
        no_strata_count = 0

        def meters_to_feet(meters):
            return meters * 3.2808399

        for idx, stand in enumerate(Stand.objects.all()):
            strata = stand.strata
            if strata and strata.stand_list['property'].index('trees_forestproperty_') == 0 and (MAX_ITERATIONS < 1 or idx < MAX_ITERATIONS):
                propid = int(strata.stand_list['property'][21:])
                prop = ForestProperty.objects.get(id=propid)
                variant = prop.variant.code
                classes = strata.stand_list['classes']
                centroid = stand.geometry_final.centroid
                centroid.transform(4326)        #stand coords are stored in 3857 projection
                site_cond = {
                        'latitude_fuzz':centroid[1],
                        'longitude_fuzz':centroid[0],
                        'calc_aspect': stand.aspect,
                        'elev_ft': meters_to_feet(stand.elevation),  #stand values are stored as meters
                        'calc_slope': stand.slope,
                        'stand_age': strata.search_age
                    }
                weight_dict=None
                k=CANDIDATES_DESIRED
                try:
                    result, num_candidates = get_nearest_neighbors(site_cond, classes, variant, weight_dict, k)
                    for rank, match in enumerate(result):  # matches come ordered by most-to-least suited. We can iterate
                        match_dicts.append({
                            'stand_id': stand.id,
                            'species_class': match['fia_forest_type_name'],
                            'variant': variant,
                            'cond_id': match.name,
                            'rank': rank+1,      # 'zero indexed' rank variable should have a '1 indexed' value
                            'certainty': match['_certainty']
                        })
                except:
                    print 'FAIL'
            else:
                miss_count += 1
                if not strata:
                    no_strata_count += 1



        out_location = '%s/../docs/output/matching_conditions.csv' % settings.BASE_DIR
        with open(out_location, 'w') as outfile:
            fieldnames = ['stand_id','species_class','variant','cond_id','rank','certainty']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)

            writer.writeheader()
            for match_dict in match_dicts:
                writer.writerow(match_dict)

        print 'Misses: %s' % str(miss_count)
        print 'Strata Misses: %s' % str(no_strata_count)
        print 'Output can be found at %s' % out_location
