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


def filter_stand_list(stand_list, min_candidates=3, tpa_factor=1.2, output="candidates_concat.csv"):

    cursor = connection.cursor()

    keep_going = True
    tpa_matches = []
    remaining = stand_list[::-1]

    while keep_going:
        where_clause_template = """(fia_forest_type_name = '%s' AND calc_dbh_class = %d)"""
        where_clause_tpa_template = """(fia_forest_type_name = '%s' AND calc_dbh_class = %d AND SumOfTPA > %f AND SumOfTPA < %f)"""

        where_clauses = [] 
        for sc in stand_list:
            if sc in tpa_matches:
                where_clauses.append(where_clause_tpa_template % (sc[0], sc[1], sc[2]/tpa_factor, sc[2]*tpa_factor))
            else:
                where_clauses.append(where_clause_template % (sc[0], sc[1]))
        where_clause = " \n                OR ".join(where_clauses)

            
        sql = """
            SELECT * FROM (
                SELECT 
                    COND_ID, 
                    SUM(SumOfTPA) as "Total_TPA",
                    SUM(SumOfBA_FT2_AC) as "Total_BAA", 
                    SUM(pct_of_totalba) as "PCT_BA",
                    COUNT(SumOfTPA) as "class_matches",
                    AVG(COUNT_SPECIESSIZECLASSES) as "class_total"
                FROM treelive_summary 
                WHERE 
                %(where_clause)s
                GROUP BY COND_ID
            ) as subselect 
            WHERE class_matches = %(num_specified_classes)s 
            ORDER BY "class_matches" DESC, "PCT_BA" DESC
        """ % { 'where_clause': where_clause, 
                'num_specified_classes': len(stand_list)}

        print sql
        cursor.execute(sql)
        local_rows = dictfetchall(cursor)

        num_candidates = len(local_rows)
        print num_candidates
        if num_candidates < 10:
            # bail, use last known good query (ie don't assign local_rows to rows)
            break

        rows = local_rows
        if num_candidates <= min_candidates or len(tpa_matches) == len(stand_list):
            keep_going = False
        else:
            tpa_matches.append(remaining.pop())


    if rows:
        df = pd.DataFrame(rows)
        df.index = df['cond_id']
        del df['cond_id']
        print df[:25]
    else:
        print "*** NADA"

    df.to_csv(output)


if __name__ == "__main__":

        # This guy matches condition 1332 almost exactly
        stand_list = [
            # species, sizeclass, tpa
            ('Douglas-fir', 6, 160),
            ('Douglas-fir', 10, 31),
            ('Douglas-fir', 14, 7),
            ('Western hemlock', 14, 5),
            #('Western redcedar', 14, 5),
            #('Red alder', 6, 40),
        ]

        filter_stand_list(stand_list, )

