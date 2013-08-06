from trees.utils import angular_diff
import numpy as np
from scipy.spatial import KDTree
import math
import pandas as pd
from django.db import connection
from django.core.cache import cache
from madrona.common.utils import get_logger
logger = get_logger()

def dictfetchall(cursor, classname=None):
    """Returns all rows from a cursor as a dict
     optionally replaces all __ with the specified classname
     ex: TPA__ becomes TPA_Douglas-Fir_14_18"""
    desc = cursor.description
    if not classname:
        res = [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
        ]
    else:
        cname = "_%s" % classname
        res = [
            dict(zip([col[0].replace("__", cname) for col in desc], row))
            for row in cursor.fetchall()
        ]
    return res


class NearestNeighborError(Exception):
    pass


def get_candidates(stand_list, variant, min_candidates=1):
    """
    Given a stand list and a variant code,
    return a list of IdbSummary instances that are potential candidate matches
    """
    cursor = connection.cursor()

    dfs = []

    key = "Candidates_" + "_".join([str(item) for sublist in stand_list
                                    for item in sublist] +
                                   [variant, str(min_candidates)])
    res = cache.get(key)
    if res is not None:
        return res

    for sc in stand_list:

        sql = """
            SELECT
                treelive_summary.COND_ID,
                SUM(SumOfTPA) as "TPA__",
                SUM(SumOfBA_FT2_AC) as "BAA__",
                SUM(pct_of_totalba) as "PCTBA__",
                AVG(COUNT_SPECIESSIZECLASSES) as "PLOTCLASSCOUNT__",
                AVG(TOTAL_BA_FT2_AC) as "PLOTBA__"
            FROM treelive_summary, trees_conditionvariantlookup as cvl
            WHERE fia_forest_type_name = %(species)s
            AND cvl.cond_id = treelive_summary.cond_id  --join
            AND cvl.variant_code = %(variant_code)s
            AND calc_dbh_class >= %(lowsize)s AND calc_dbh_class < %(highsize)s
            AND pct_of_totalba is not null
            GROUP BY treelive_summary.COND_ID
        """
        inputs = {
            'species': sc[0],
            'lowsize': int(sc[1]),
            'highsize': int(sc[2]),
            'variant_code': variant
        }

        classname = "%(species)s_%(lowsize)s_%(highsize)s" % inputs

        cursor.execute(sql, inputs)
        rows = dictfetchall(cursor, classname)

        if not rows:
            raise NearestNeighborError(
                "No matches for %s, %s to %s in" % (sc[0], sc[1], sc[2]))

        df = pd.DataFrame(rows)
        df.index = df['cond_id']
        del df['cond_id']
        dfs.append(df)

    if len(dfs) == 0:
        raise NearestNeighborError("The stand list provided does not yield enough matches.")
    elif len(dfs) == 1:
        sdfs = dfs
    else:
        sdfs = sorted(dfs, key=lambda x: len(x), reverse=True)

    enough = False
    while not enough:
        if len(sdfs) == 0:
            raise NearestNeighborError("The stand list provided does not yield enough matches.")
        candidates = pd.concat(sdfs, axis=1, join="inner")
        if len(candidates) < min_candidates:
            aa = sdfs.pop()  # remove the one with smallest number
            logger.warn("Popping %s ", [x.replace("BAA_", "")
                                        for x in aa.columns.tolist()
                                        if x.startswith('BAA_')][0]
                        )

            continue
        else:
            enough = True

        # Percentage of the plot basal area comprised of the specified species/size classes
        # Note that this should be ~= TOTAL_BA / PLOT_BA
        candidates['TOTAL_PCTBA'] = candidates[[
            x for x in candidates.columns if x.startswith('PCTBA')]].sum(axis=1)
        # Total basal area of the specified species/size classes
        candidates['TOTAL_BA'] = candidates[[
            x for x in candidates.columns if x.startswith('BAA')]].sum(axis=1)
        # Total trees per acre of the specified species/size classes
        candidates['TOTAL_TPA'] = candidates[[
            x for x in candidates.columns if x.startswith('TPA')]].sum(axis=1)
        # Number of unique 2" species/size classes in the plot
        candidates['PLOT_CLASS_COUNT'] = candidates[[
            x for x in candidates.columns if x.startswith('PLOTCLASSCOUNT')]].mean(axis=1)
        # Number of specified species/size classes
        candidates['SEARCH_CLASS_COUNT'] = len(stand_list)
        # Basal area of the entire plot
        candidates['PLOT_BA'] = candidates[[
            x for x in candidates.columns if x.startswith('PLOTBA')]].mean(axis=1)

        for x in candidates.columns:
            if x.startswith('PLOTCLASSCOUNT_') or x.startswith("PLOTBA_"):
                del candidates[x]

        sql = """
            SELECT
                COND_ID,
                SUM(SumOfTPA) as "NONSPEC_TPA",
                SUM(SumOfBA_FT2_AC) as "NONSPEC_BA"
            FROM treelive_summary
            WHERE fia_forest_type_name NOT IN (%s)
            AND pct_of_totalba is not null
            GROUP BY COND_ID
        """
        species_list = [sc[0] for sc in stand_list]
        in_p = ', '.join(['%s'] * len(stand_list))
        sql = sql % in_p
        cursor.execute(sql, species_list)
        rows = dictfetchall(cursor, classname)

        df = pd.DataFrame(rows)
        df.index = df['cond_id']
        del df['cond_id']

        candidates = candidates.join(df)
        candidates = candidates.fillna(0)  # if nonspec basal area is nan, make it zero

    cache.set(key, candidates, timeout=0)
    return candidates


def get_sites(candidates):
    """ query for and return a dataframe of cond_id + site variables """
    cursor = connection.cursor()
    sql = """
        SELECT *
            -- COND_ID, calc_aspect, calc_slope
        FROM idb_summary
        WHERE COND_ID IN (%s)
        AND stand_age is not null
    """ % (",".join([str(int(x)) for x in candidates.index.tolist()]))

    cursor.execute(sql)
    rows = dictfetchall(cursor)

    if rows:
        df = pd.DataFrame(rows)
        df.index = df['cond_id']
        del df['cond_id']
        return df
    else:
        raise NearestNeighborError("No sites returned")


def get_nearest_neighbors(site_cond, stand_list, variant, weight_dict=None, k=10, verbose=False):
    """
    Primary entry point to nearest neighbor matching
    Function to determine the k nearest plots in attribute space

    inputs:
      - site_cond: dict of site conditions (elevation, aspect, slope, lat, lon)
      - stand_list: list of tuples; [("speciesname", min_dbh, max_dbh, tpa),...] 
      - variant: 2-letter variant code to filter by
      - weight_dict: dict, weighting for each input_param. assumes 1 if not in dict.

    outputs:
      - list of k IdbSummary instances
      - total number of potential candidates
    """

    # process stand_list into dict
    tpa_dict = {}
    ba_dict = {}
    total_tpa = 0
    total_ba = 0
    for ssc in stand_list:
        key = '_'.join([str(x) for x in ssc[0:3]])
        total_tpa += ssc[3]
        tpa_dict[key] = ssc[3]

        ## est_ba = tpa * (0.005454 * dbh^2)
        est_ba = ssc[3] * (0.005454 * (((ssc[1] + ssc[2]) / 2.0) ** 2.0))
                           # assume middle of class
        total_ba += est_ba
        ba_dict[key] = est_ba

    if verbose:
        print "----- estimated total basal area", total_ba

    # query for candidates
    candidates = get_candidates(stand_list, variant)

    # query for site variables and create dataframe
    sites = get_sites(candidates)

    # merge site data with candidates
    # candidates U site
    plotsummaries = pd.concat([candidates, sites], axis=1, join="inner")

    input_params = {}
    for attr in plotsummaries.axes[1].tolist():
        if attr.startswith("BAA_"):
            ssc = attr.replace("BAA_", "")
            input_params[attr] = ba_dict[ssc]
        elif attr.startswith("TPA_"):
            ssc = attr.replace("TPA_", "")
            input_params[attr] = tpa_dict[ssc]
        elif attr == "TOTAL_PCTBA":
            input_params[attr] = 100.0  # TODO don't assume 100%
        elif attr == "PLOT_BA":
            input_params[attr] = total_ba
        elif attr == "NONSPEC_BA":
            input_params[attr] = 0  # shoot for 0 ba from non-specified species
        elif attr == "NONSPEC_TPA":
            input_params[attr] = 0  # shoot for 0 tpa from non-specified species
        elif attr == "TOTAL_TPA":
            input_params[attr] = total_tpa

    # Add site conditions
    input_params.update(site_cond)

    if not weight_dict:
        weight_dict = {}

    nearest = nearest_plots(input_params, plotsummaries, weight_dict, k, verbose)

    return nearest


class NoPlotMatchError:
    pass


def nearest_plots(input_params, plotsummaries, weight_dict=None, k=10, verbose=True):
    """
    Utility function to determine the k nearest plots in attribute space

    inputs:
      - input_params: dict of numeric variables for kdtree matching
      - plotsummaries: list of candidate IdbSummary instances
      - weight_dict: dict, weighting for each input_param. assumes 1 if not in dict.

    outputs:
      - list of k IdbSummary instances
      - total number of potential candidates
    """
    if not weight_dict:
        # default weight dict
        weight_dict = {
            'TOTAL_PCTBA': 10.0,
            'PLOT_BA': 5.0,
            'NONSPEC_BA': 10.0,
            'NONSPEC_TPA': 5.0,
            'TOTAL_TPA': 2.0,
            'stand_age': 25.0,
            'calc_slope': 0.5,
            'calc_aspect': 1.0,
            'elev_ft': 0.75,
        }

    search_params = input_params.copy()
    origkeys = search_params.keys()
    keys = [x for x in origkeys if x not in ['calc_aspect', ]]  # special case

    # assert that we have some candidates
    num_candidates = len(plotsummaries)
    if num_candidates == 0:
        raise NoPlotMatchError("There are no candidate plots")

    ps_attr_list = []
    for cond_id in plotsummaries.index.tolist():
        ps = plotsummaries.ix[cond_id]

        vals = []
        for attr in keys:
            vals.append(ps[attr])

        # Aspect is a special case
        if 'calc_aspect' in origkeys:
            angle = angular_diff(
                ps['calc_aspect'], input_params['calc_aspect'])
            vals.append(angle)
            search_params['_aspect'] = 0  # anglular difference to self is 0

        ps_attr_list.append(vals)

    # include our special case
    if 'calc_aspect' in origkeys:
        keys.append('_aspect')

    weights = np.ones(len(keys))
    for i in range(len(keys)):
        key = keys[i]
        if key in weight_dict:
            weights[i] = weight_dict[key]

    if verbose:
        table_data = []
        headers = keys
        table_data.append(([round(x, 2) for x in list(weights)], 'Weights'))

    querypoint = np.array([round(search_params[attr], 2) for attr in keys])
    rawpoints = np.array(ps_attr_list)

    # Normalize to standard deviations from mean
    stds = np.std(rawpoints, axis=0)
    means = np.mean(rawpoints, axis=0)
    if verbose:
        table_data.append(([round(x, 2) for x in means.tolist()], 'Means'))
        table_data.append(([round(x, 2) for x in stds.tolist()], 'Std devs'))
    scaled_points = (rawpoints - means) / stds
    scaled_querypoint = (querypoint - means) / stds
    scaled_querypoint[np.isinf(scaled_querypoint)] = 0

    if verbose:
        raw_querypoint = [float(x) for x in list(querypoint)]
        table_data.append((list(raw_querypoint), 'Raw querypoint'))
        sqp = [round(x, 2) for x in list(scaled_querypoint)]
        table_data.append((sqp, 'scaled querypoint'))

    # Apply weights
    # and guard against any nans due to zero range or other
    scaled_points = np.nan_to_num(scaled_points * weights)
    scaled_querypoint = np.nan_to_num(scaled_querypoint * weights)

    if verbose:
        sqp = [round(x, 2) for x in list(scaled_querypoint)]
        table_data.append((sqp, 'scaled/weighted querypoint'))

    # Create tree and query it for nearest plot
    tree = KDTree(scaled_points)
    querypoints = np.array([scaled_querypoint])
    result = tree.query(querypoints, k=k)
    distances = result[0][0]
    plots = result[1][0]

    top = zip(plots, distances)
    ps = []

    xs = [100 * x for x in weights if x > 0]
    squares = [x * x for x in xs]
    max_dist = math.sqrt(sum(squares))  # the real max
    for t in top:
        if np.isinf(t[1]):
            continue
        try:
            pseries = plotsummaries.irow(t[0])
            if verbose:
                sp = [round(x, 2) for x in list(scaled_points[t[0]])]
                table_data.append((sp, 'scaled/weighted candidate %s' % pseries.name))
        except IndexError:
            continue

        # certainty of 0 -> distance is furthest possible
        # certainty of 1 -> the point matches exactly
        # sqrt of ratio taken to exagerate small diffs
        pseries = pseries.set_value('_kdtree_distance', t[1])
        pseries = pseries.set_value(
            '_certainty', 1.0 - ((t[1] / max_dist) ** 0.5))

        ps.append(pseries)

    if verbose:
        print "".join(["%-32s" % ("| " + x) for x in headers[::4]])
        print " "*8 + "".join(["%-32s" % ("| " + x) for x in headers[1::4]])
        print " "*16 + "".join(["%-32s" % ("| " + x) for x in headers[2::4]])
        print " "*24 + "".join(["%-32s" % ("| " + x) for x in headers[3::4]])
        print "|-------" * (len(headers) + 1)

        for td in table_data:
            print "".join(["%8s" % str(x) for x in td[0]]), td[1]

    return ps, num_candidates
