import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', '..', '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)

##############################
import pandas as pd
from django.db import connection

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

if __name__ == "__main__":

        cursor = connection.cursor()

        # This guy matches condition 1332 almost exactly
        stand_list = [
            # species, sizeclass, tpa
            ('Douglas-fir', 6, 560),
            ('Douglas-fir', 10, 31),
            ('Douglas-fir', 14, 7),
            ('Western hemlock', 14, 5),
            ('Western redcedar', 14, 5),
            #('Red alder', 6, 40),
        ]

        MIN_CANDIDATES = 6 
        MAX_TPA_FACTOR = 10 # we tolerate, at most +/- X x TPA
        tpa_factor = 1.2

        num_candidates = 0
        skip_species = []

        while num_candidates < MIN_CANDIDATES:
            dfs = []

            tpa_factor = tpa_factor ** 1.5
            if tpa_factor > MAX_TPA_FACTOR:
                raise Exception("The stand list provided does not provide enough matches, even with very high tolerances for density variation")

            print "Trying with TPA factor +/- %s x ...."  % tpa_factor

            for sc in stand_list:
                if (sc[0], sc[1]) in skip_species:
                    continue

                num_class_candidates = 0
                local_tpa_factor = tpa_factor
                while num_class_candidates < MIN_CANDIDATES:

                    # This could potentially be used to dynamically expand the size range
                    # class_clause = 'AND calc_dbh_class >= %d AND calc_dbh_class <= %d' % (sc[1] - 2, sc[1] + 2) 

                    if local_tpa_factor > MAX_TPA_FACTOR:
                        rows = None
                        skip_species.append((sc[0], sc[1]))
                        print "  ** Skipping species ... %s, %s" % (sc[0], sc[1])
                        break   # effectively skip this species if we can't find a match within an order of magnitude

                    class_clause = 'AND calc_dbh_class = %d' % (sc[1],) 

                    sql = """
                        SELECT 
                            COND_ID, 
                            SUM(SumOfTPA) as "TPA_%(species)s_%(size)d",
                            SUM(SumOfBA_FT2_AC) as "BAA_%(species)s_%(size)d", 
                            SUM(pct_of_totalba) as "PCTBA_%(species)s_%(size)d" 
                        FROM treelive_summary 
                        WHERE fia_forest_type_name = '%(species)s' 
                        %(class_clause)s
                        AND SumOfTPA >= %(low)f 
                        AND SumOfTPA <= %(high)f 
                        AND pct_of_totalba is not null
                        GROUP BY COND_ID
                    """ % { 'class_clause': class_clause, 
                            'species': sc[0], 
                            'size': sc[1], 
                            'low': sc[2] / local_tpa_factor, 
                            'high': sc[2] * local_tpa_factor}

                    cursor.execute(sql)
                    rows = dictfetchall(cursor)
                    num_class_candidates = len(rows)
                    print "  %s %s - Trying with LOCAL TPA factor +/- %s x .... %d candidates"  % (sc[0], sc[1], local_tpa_factor, num_class_candidates)
                    local_tpa_factor += 2 

                if rows:
                    df = pd.DataFrame(rows)
                    df.index = df['cond_id']
                    del df['cond_id']
                    dfs.append(df)

            if len(dfs) == 0:
                raise Exception("The stand list provided does not provide enough matches, even with very high tolerances for density variation")

            candidates = pd.concat(dfs, axis=1, join="inner")
            num_candidates = len(candidates)
            print "  INTERSECTION OF ALL SPECIES/SIZE CLASSES.... %d candidates"  % (num_candidates, )

        print "Got %d candidates" % (num_candidates, )
        print " Density range: +/- %f x TPA " % tpa_factor
        if skip_species:
            print " Skipped invalid species classes: %s " % skip_species
        else:
            print " All species accounted for." % skip_species
        candidates['sumall'] = candidates[[x for x in candidates.columns if x.startswith('PCTBA')]].sum(axis=1)
        output = 'candidates_concat.tsv'
        candidates.to_csv(output, sep="\t")
        print " See output in %s" % output

