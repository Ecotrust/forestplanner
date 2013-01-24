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

        stand_list = [
            # species, sizeclass, tpa
            ('Douglas-fir', 10, 85),
            ('Douglas-fir', 14, 29),
            ('Western hemlock', 22, 2),
            ('Red alder', 6, 40),
        ]

        dfs = []

        for sc in stand_list:

            sql = """
                SELECT 
                    COND_ID, 
                    SumOfTPA as "TPA_%(species)s_%(size)d",
                    SumOfBA_FT2_AC as "BAA_%(species)s_%(size)d", 
                    pct_of_totalba as "PCTBA_%(species)s_%(size)d" 
                FROM treelive_summary 
                WHERE fia_forest_type_name = '%(species)s' 
                AND calc_dbh_class = %(size)d 
                AND SumOfTPA >= %(low)f 
                AND SumOfTPA <= %(high)f 
                AND pct_of_totalba is not null
            """ % {'species': sc[0], 'size': sc[1], 'low': sc[2]/3.0, 'high': sc[2] * 3.0}

            cursor.execute(sql)
            rows = dictfetchall(cursor)
            df = pd.DataFrame(rows)
            df.index = df['cond_id']
            del df['cond_id']
            dfs.append(df)

        test = pd.concat(dfs, axis=1, join="inner")

        test['sumall'] = test[[x for x in test.columns if x.startswith('PCTBA')]].sum(axis=1)
        test.to_csv('test_concat.csv')
