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

        OUTFILE_NAME = 'match_debug_20160211'
        CANDIDATES_DESIRED = 10  # How many candidates would you like?
        MAX_ITERATIONS = 10      # <1 for 'run all'

        match_dicts = []
        miss_count = 0
        no_strata_count = 0

        def meters_to_feet(meters):
            return meters * 3.2808399

        # for idx, stand in enumerate(Stand.objects.filter(id__range=[7856, 7886])):
        for idx, stand in enumerate(Stand.objects.all()):
            if idx % 200 == 0:
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
                        # if stand.id > 7855 and stand.id < 7887:
                        result, num_candidates = get_nearest_neighbors(site_cond, classes, variant, weight_dict, k)
                        # import ipdb
                        # ipdb.set_trace()
                        for rank, match in enumerate(result):  # matches come ordered by most-to-least suited. We can iterate
                            match_classes = []
                            for stand_class in classes:
                                tpa_key = 'TPA_%s_%d_%d' % (stand_class[0], stand_class[1], stand_class[2])
                                if tpa_key in match.index:
                                    match_classes.append([stand_class[0], stand_class[1], stand_class[2], match[tpa_key]])
                            cond_treelist = []
                            summaries = TreeliveSummary.objects.filter(cond_id=match.name , variant=variant)
                            for summary in summaries:
                                cond_treelist.append(summary.treelist)
                            cond_data = {}
                            for key in match.keys():
                                cond_data[key] = match[key]

                            match_dicts.append({
                                'stand_id': stand.id,
                                'species_class': match['fia_forest_type_name'],
                                'variant': variant,
                                'cond_id': match.name,
                                'rank': rank+1,      # 'zero indexed' rank variable should have a '1 indexed' value
                                'certainty': match['_certainty'],
                                'site_cond': str(site_cond),
                                'classes': str(classes),
                                'match_cond': "{'calc_aspect': %f, 'elev_ft': %f, 'latitude_fuzz': %f, 'longitude_fuzz': %f, 'calc_slope': %f, 'stand_age': %f}" % (match['calc_aspect'], match['elev_ft'], match['latitude_fuzz'], match['longitude_fuzz'], match['calc_slope'], match['stand_age']),
                                'match_classes': match_classes,
                                'cond_treelist': cond_treelist,
                                'cond_data': cond_data
                            })
                    except:
                        print 'FAIL'
                else:
                    miss_count += 1
                    if not strata:
                        no_strata_count += 1



        out_location = '%s/../docs/output/%s.csv' % (settings.BASE_DIR, OUTFILE_NAME)
        with open(out_location, 'w') as outfile:
            fieldnames = ['stand_id','species_class','variant','cond_id','rank','certainty','site_cond','classes','match_cond','match_classes','cond_treelist', 'cond_data']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)

            writer.writeheader()
            for match_dict in match_dicts:
                writer.writerow(match_dict)

        print 'Misses: %s' % str(miss_count)
        print 'Strata Misses: %s' % str(no_strata_count)
        print 'Output can be found at %s' % out_location
