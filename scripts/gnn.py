import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
from itertools import *
from django.db import connection

def qry(query_string, *query_args):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, query_args)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(izip(col_names, row))
        yield row_dict
    return

def get_data(fortypiv, vegclass):
    sql = """
    SELECT * 
    FROM sppsz_attr_all A, trees_gnn_orwa B 
    WHERE B.value = A.value
    AND A.fortypiv = %s
    AND A.vegclass = %s 
    """ 
    return list(qry(sql, fortypiv, vegclass))


import matplotlib
# chose a non-GUI backend
matplotlib.use( 'Agg' )
import pylab

######################


def main(fortypiv, vegclass):
    if not fortypiv:
        return None
    data = get_data(fortypiv, vegclass)
    fortypiv = fortypiv.replace("/","-")

    def plot(data, name):
        pylab.hist(data, bins=20)
        pylab.savefig( "/var/www/labs/gnn/img/%s_%s_%s.png" % (fortypiv, vegclass, name), format='png' )
        pylab.clf()

    def html(data, name):
        html = "<h1>%s for </h1> <h2>Fortypiv: %s</h2><h2>Vegclass: %s</h2>" % (name, fortypiv, vegclass)
        html += "<p>records: %s, min: %s, mean: %s, max: %s </p>" % (len(vals), min(vals), sum(vals)/float(len(vals)), max(vals))
        html += '<img src="./img/%s_%s_%s.png" />' % (fortypiv, vegclass, name)
        with open('/var/www/labs/gnn/%s_%s_%s.html' % (fortypiv, vegclass, name), 'w') as fh:
            fh.write(html)


    vars = [ 
        #('stand_height', 'stndhgt'), 
        #('density', 'sdi'), 
        #('treesperhectare', 'tph_ge_3'), 
        #('basalarea', 'baa_ge_3'), 
        ('age', 'age_dom'), 
        ]

    for var in vars:
        name = var[0]
        vals = [d[var[1]] for d in data]
        html(vals, name)
        plot(vals, name)
        print '/var/www/labs/gnn/%s_%s_%s.html' % (fortypiv, vegclass, name)

fortypiv = 'PSME'
vegclass = 9
def get_cats():
    sql = """
    SELECT fortypiv, vegclass, count(fcid) as cnt
    FROM sppsz_attr_all A, trees_gnn_orwa B 
    WHERE B.value = A.value
    GROUP BY fortypiv, vegclass
    """ 
    return [(x['fortypiv'], x['vegclass']) for x in list(qry(sql)) if x['cnt'] > 25]

cats = get_cats()
for cat in cats:
    fortypiv = cat[0]
    vegclass = cat[1]
    #main(fortypiv, vegclass)

main('PSME',9)
