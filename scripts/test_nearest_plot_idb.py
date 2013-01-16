import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)

##############################
from trees.utils import potential_minmax, nearest_plots
from trees.models import PlotLookup
import itertools

if __name__ == "__main__":
 
    test_cases = [
        (
            { 
                'for_type_name': 'Douglas-fir', 
                #'for_type_name': 'Red alder', 
            }, 
            {
                'age_dom': 40,
                'qmda_dom_stunits': 15,
                'tph_ge_3_stunits': 250,
                'baa_ge_3_stunits': 26,
                'elev_ft': 1279,
                'calc_slope': 25,
                'calc_aspect': 225, 
                'longitude_fuzz': -123.0, 
                'latitude_fuzz': 43.0, 
            },
            ['age_dom', 'qmda_dom_stunits', 'tph_ge_3_stunits', 'baa_ge_3_stunits']
        ),

        (
            { 
                'for_type_name': 'Douglas-fir', 
                'for_type_secdry_name': 'Red alder', 
            }, 
            {
                'age_dom': 40,
                'qmda_dom_stunits': 15,
                'tph_ge_3_stunits': 250,
                'baa_ge_3_stunits': 26,
                'elev_ft': 1279,
                'calc_slope': 25,
                'calc_aspect': 225, 
                'longitude_fuzz': -123.0, 
                'latitude_fuzz': 43.0, 
            },
            ['age_dom', 'qmda_dom_stunits', 'tph_ge_3_stunits', 'baa_ge_3_stunits']
        ),
    ]

    
    weight_dict = {}
    keys = [str(x.attr) for x in PlotLookup.objects.all()]  
    print ','.join(['plotid','certainty', 'num_candidates'] + ['input_' + k for k in keys] + ['known_' + k for k in keys] + keys)

    for case in test_cases:
        categories = case[0]
        original_input_params = case[1]
        all_attrs_for_removal = case[2]

        combos_for_removal = [ () ]
        for n in range(1, len(all_attrs_for_removal)):
            for i in itertools.combinations(all_attrs_for_removal, n):
                combos_for_removal.append(i)

        for attrs_for_removal in combos_for_removal:
            input_params = original_input_params.copy()
            for attr in attrs_for_removal:
                del input_params[attr]

            pmm = potential_minmax(categories, weight_dict, input_params)
            top, num_candidates = nearest_plots(categories, input_params, weight_dict, k=2)

            all_inputs = dict(input_params.items() + categories.items())
            all_knowns = dict(original_input_params.items() + categories.items())

            for plot in top[:1]:
                print ','.join(
                    [str(plot.cond_id), str(plot._certainty), str(num_candidates)] +
                    [str(all_inputs[x]) if x in all_inputs.keys() else '--' for x in keys] + 
                    [str(all_knowns[x]) if x in all_knowns.keys() else '--' for x in keys] + 
                    [str(plot.__dict__[x]) for x in keys]
                )
