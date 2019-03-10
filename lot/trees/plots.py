from trees.utils import angular_diff
import numpy as np
from scipy.spatial import KDTree
import math
import pandas as pd
from django.db import connection
from django.core.cache import cache
from django.conf import settings
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


def get_candidates(stand_list, variant, min_candidates=1, verbose=False):
    """
    Given a stand list and a variant code,
    return a list of IdbSummary instances that are potential candidate matches
    The stand_list values come from the user when defining forest type.
    """
    cursor = connection.cursor()

    dfs = []

    # Key is used for caching only
    key = "Candidates_" + "_".join([str(item) for sublist in stand_list
                                    for item in sublist] +
                                   [variant, str(min_candidates)])

    res = cache.get(key)
    if res is not None:
        return res

    common_species_lookup = {
        "Vine maple": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "VN", "SO": "CH", "COMMON_NAME": "Vine maple", "PN": "CH"},
        "Fan palm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Fan palm", "PN": "OT"},
        "Common hoptree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Common hoptree", "PN": "OT"},
        "Sweet bay": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Sweet bay", "PN": "OT"},
        "Arizona white oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Arizona white oak", "PN": "OT"},
        "Paradox acacia": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Paradox acacia", "PN": "OT"},
        "Limber pine": {"WC": "OT", "BM": "LM", "CA": "LM", "EC": "WB", "SO": "WB", "COMMON_NAME": "Limber pine", "PN": "OT"},
        "Mexican blue oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Mexican blue oak", "PN": "OT"},
        "Beach pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Beach pine", "PN": "LP"},
        "American sycamore": {"WC": "OT", "BM": "OH", "CA": "SY", "EC": "OH", "SO": "OH", "COMMON_NAME": "American sycamore", "PN": "OT"},
        "Silverleaf oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Silverleaf oak", "PN": "OT"},
        "Pacific willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Pacific willow", "PN": "WI"},
        "Pacific dogwood": {"WC": "DG", "BM": "OH", "CA": "DG", "EC": "DG", "SO": "OH", "COMMON_NAME": "Pacific dogwood", "PN": "DG"},
        "Bigcone Douglas-fir": {"WC": "DF", "BM": "DF", "CA": "OS", "EC": "DF", "SO": "OS", "COMMON_NAME": "Bigcone Douglas-fir", "PN": "DF"},
        "Oregon crabapple": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "OH", "COMMON_NAME": "Oregon crabapple", "PN": "OT"},
        "Fragrant ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Fragrant ash", "PN": "OT"},
        "Arizona sycamore": {"WC": "OT", "BM": "OH", "CA": "SY", "EC": "OH", "SO": "OH", "COMMON_NAME": "Arizona sycamore", "PN": "OT"},
        "Chinquapin spp.": {"WC": "GC", "BM": "OH", "CA": "GC", "EC": "GC", "SO": "GC", "COMMON_NAME": "Chinquapin spp.", "PN": "GC"},
        "Larch spp.": {"WC": "YC", "BM": "WL", "CA": "OS", "EC": "WL", "SO": "WL", "COMMON_NAME": "Larch spp.", "PN": "YC"},
        "Lilac spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Lilac spp.", "PN": "OT"},
        "Black hawthorn": {"WC": "HT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Black hawthorn", "PN": "HT"},
        "Bur oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Bur oak", "PN": "OT"},
        "Rio Grande cottonwood": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Rio Grande cottonwood", "PN": "CW"},
        "Lanceleaf cottonwood": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Lanceleaf cottonwood", "PN": "CW"},
        "Knowlton's hophornbeam": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Knowlton's hophornbeam", "PN": "OT"},
        "Black walnut": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Black walnut", "PN": "OT"},
        "California nutmeg": {"WC": "OT", "BM": "OS", "CA": "CN", "EC": "OS", "SO": "OS", "COMMON_NAME": "California nutmeg", "PN": "OT"},
        "Pistache": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Pistache", "PN": "OT"},
        "Plum/cherry spp.": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "CH", "COMMON_NAME": "Plum/cherry spp.", "PN": "CH"},
        "Willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "PN": "WI"},
        "Goldenrain tree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Goldenrain tree", "PN": "OT"},
        "Juniper spp.": {"WC": "WJ", "BM": "WJ", "CA": "WJ", "EC": "WJ", "SO": "WJ", "COMMON_NAME": "Juniper spp.", "PN": "WJ"},
        "Unknown spp.": {"WC": "OT", "BM": "OS", "CA": "OH", "EC": "OS", "SO": "OS", "COMMON_NAME": "Unknown spp.", "PN": "OT"},
        "Sweet acacia": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Sweet acacia", "PN": "OT"},
        "Sonoran scrub oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Sonoran scrub oak", "PN": "OT"},
        "Texas madrone": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Texas madrone", "PN": "OT"},
        "Siberian alder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "RA", "SO": "OH", "COMMON_NAME": "Siberian alder", "PN": "OT"},
        "Sweet cherry": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "CH", "COMMON_NAME": "Sweet cherry", "PN": "CH"},
        "Narrowleaf cottonwood": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Narrowleaf cottonwood", "PN": "CW"},
        "Mt. Atlas mastic tree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Mt. Atlas mastic tree", "PN": "OT"},
        "Italian alder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "RA", "SO": "OH", "COMMON_NAME": "Italian alder", "PN": "OT"},
        "Spruce spp.": {"WC": "ES", "BM": "ES", "CA": "BR", "EC": "ES", "SO": "ES", "COMMON_NAME": "Spruce spp.", "PN": "SS"},
        "Crack willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Crack willow", "PN": "WI"},
        "Modoc cypress": {"WC": "OT", "BM": "WJ", "CA": "WJ", "EC": "WJ", "SO": "WJ", "COMMON_NAME": "Modoc cypress", "PN": "OT"},
        "Green wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Green wattle", "PN": "OT"},
        "Mountain hemlock": {"WC": "MH", "BM": "MH", "CA": "MH", "EC": "MH", "SO": "MH", "COMMON_NAME": "Mountain hemlock", "PN": "MH"},
        "Edible fig": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Edible fig", "PN": "OT"},
        "Engelmann spruce": {"WC": "ES", "BM": "ES", "CA": "BR", "EC": "ES", "SO": "ES", "COMMON_NAME": "Engelmann spruce", "PN": "ES"},
        "Cootamundra wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Cootamundra wattle", "PN": "OT"},
        "California juniper": {"WC": "WJ", "BM": "WJ", "CA": "WJ", "EC": "WJ", "SO": "WJ", "COMMON_NAME": "California juniper", "PN": "WJ"},
        "Silverberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Silverberry", "PN": "OT"},
        "Ponderosa pine": {"WC": "PP", "BM": "PP", "CA": "PP", "EC": "PP", "SO": "PP", "COMMON_NAME": "Ponderosa pine", "PN": "PP"},
        "California buckeye": {"WC": "OT", "BM": "OH", "CA": "BU", "EC": "OH", "SO": "OH", "COMMON_NAME": "California buckeye", "PN": "OT"},
        "Balm-of-Gilead": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Balm-of-Gilead", "PN": "CW"},
        "Resin birch": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "PB", "SO": "OH", "COMMON_NAME": "Resin birch", "PN": "OT"},
        "Pine": {"WC": "OT", "BM": "OS", "CA": "MP", "EC": "OS", "SO": "OS", "COMMON_NAME": "Pine", "PN": "OT"},
        "Sugarberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Sugarberry", "PN": "OT"},
        "Port Jackson fig": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Port Jackson fig", "PN": "OT"},
        "Coral gum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Coral gum", "PN": "OT"},
        "Oregon white oak": {"WC": "WO", "BM": "OH", "CA": "WO", "EC": "WO", "SO": "WO", "COMMON_NAME": "Oregon white oak", "PN": "WO"},
        "Silver wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Silver wattle", "PN": "OT"},
        "Huckleberry oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Huckleberry oak", "PN": "OT"},
        "Alaska yellow-cedar": {"WC": "YC", "BM": "YC", "CA": "PC", "EC": "YC", "SO": "OS", "COMMON_NAME": "Alaska yellow-cedar", "PN": "YC"},
        "Western paper birch": {"WC": "PB", "BM": "OH", "CA": "OH", "EC": "PB", "SO": "OH", "COMMON_NAME": "Western paper birch", "PN": "PB"},
        "Engelmann oak": {"WC": "OT", "BM": "OH", "CA": "EO", "EC": "OH", "SO": "OH", "COMMON_NAME": "Engelmann oak", "PN": "OT"},
        "Apple spp.": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "OH", "COMMON_NAME": "Apple spp.", "PN": "CH"},
        "Gum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Gum", "PN": "OT"},
        "Thuja spp.": {"WC": "RC", "BM": "GF", "CA": "RC", "EC": "RC", "SO": "RC", "COMMON_NAME": "Thuja spp.", "PN": "RC"},
        "Unknown dead hardwood": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Unknown dead hardwood", "PN": "OT"},
        "Screwbean mesquite  ": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Screwbean mesquite  ", "PN": "OT"},
        "Feltleaf willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Feltleaf willow", "PN": "WI"},
        "Pacific yew": {"WC": "PY", "BM": "PY", "CA": "PY", "EC": "PY", "SO": "PY", "COMMON_NAME": "Pacific yew", "PN": "PY"},
        "American holly": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "American holly", "PN": "OT"},
        "Paradise apple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Paradise apple", "PN": "OT"},
        "California sycamore": {"WC": "OT", "BM": "OH", "CA": "SY", "EC": "OH", "SO": "OH", "COMMON_NAME": "California sycamore", "PN": "OT"},
        "Velvet ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Velvet ash", "PN": "OT"},
        "California flannelbush": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "California flannelbush", "PN": "OT"},
        "Common pinyon": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Common pinyon", "PN": "OT"},
        "Southwestern white pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Southwestern white pine", "PN": "OT"},
        "Arizona pinyon pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Arizona pinyon pine", "PN": "OT"},
        "California fan palm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "California fan palm", "PN": "OT"},
        "Redbox": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Redbox", "PN": "OT"},
        "California pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "California pine", "PN": "OT"},
        "Norway maple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Norway maple", "PN": "OT"},
        "Rocky Mountain maple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "VN", "SO": "OH", "COMMON_NAME": "Rocky Mountain maple", "PN": "OT"},
        "White alder": {"WC": "WA", "BM": "OH", "CA": "RA", "EC": "RA", "SO": "WA", "COMMON_NAME": "White alder", "PN": "WA"},
        "Gray oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Gray oak", "PN": "OT"},
        "Birch": {"WC": "PB", "BM": "OH", "CA": "OH", "EC": "PB", "SO": "OH", "COMMON_NAME": "Birch", "PN": "PB"},
        "Mountain mahogany": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "MB", "COMMON_NAME": "Mountain mahogany", "PN": "OT"},
        "Viscid acacia": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Viscid acacia", "PN": "OT"},
        "Common juniper": {"WC": "WJ", "BM": "WJ", "CA": "WJ", "EC": "WJ", "SO": "WJ", "COMMON_NAME": "Common juniper", "PN": "WJ"},
        "Peppertree spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Peppertree spp.", "PN": "OT"},
        "Cottonwood spp.": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Cottonwood spp.", "PN": "CW"},
        "Lombardy poplar": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Lombardy poplar", "PN": "CW"},
        "Torrey maple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "VN", "SO": "OH", "COMMON_NAME": "Torrey maple", "PN": "OT"},
        "Honey mesquite  ": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Honey mesquite  ", "PN": "OT"},
        "Honey mesquite": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Honey mesquite", "PN": "OT"},
        "California ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "California ash", "PN": "OT"},
        "Pearl wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Pearl wattle", "PN": "OT"},
        "Arroyo willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Arroyo willow", "PN": "WI"},
        "Hairy mountain mahogany": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "MB", "COMMON_NAME": "Hairy mountain mahogany", "PN": "OT"},
        "Whitebark pine": {"WC": "WB", "BM": "WB", "CA": "WB", "EC": "WB", "SO": "WB", "COMMON_NAME": "Whitebark pine", "PN": "WB"},
        "Sweetgum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Sweetgum", "PN": "OT"},
        "Southern catalpa": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Southern catalpa", "PN": "OT"},
        "Chinkapin oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Chinkapin oak", "PN": "OT"},
        "Netleaf oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Netleaf oak", "PN": "OT"},
        "Douglas maple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "VN", "SO": "OH", "COMMON_NAME": "Douglas maple", "PN": "OT"},
        "Common linden": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Common linden", "PN": "OT"},
        "Willow spp.": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Willow spp.", "PN": "WI"},
        "English elm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "English elm", "PN": "OT"},
        "Bristlecone pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "WB", "SO": "OS", "COMMON_NAME": "Bristlecone pine", "PN": "OT"},
        "Brown dogwood": {"WC": "DG", "BM": "OH", "CA": "DG", "EC": "DG", "SO": "OH", "COMMON_NAME": "Brown dogwood", "PN": "DG"},
        "Black spruce": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "ES", "SO": "OS", "COMMON_NAME": "Black spruce", "PN": "OT"},
        "Prairie acacia": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Prairie acacia", "PN": "OT"},
        "Arizona alder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "RA", "SO": "OH", "COMMON_NAME": "Arizona alder", "PN": "OT"},
        "Whiteflower kurrajong": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Whiteflower kurrajong", "PN": "OT"},
        "Sycamore spp.": {"WC": "OT", "BM": "OH", "CA": "SY", "EC": "OH", "SO": "OH", "COMMON_NAME": "Sycamore spp.", "PN": "OT"},
        "Alder spp.": {"WC": "RA", "BM": "OH", "CA": "RA", "EC": "RA", "SO": "RA", "COMMON_NAME": "Alder spp.", "PN": "RA"},
        "Red alder": {"WC": "RA", "BM": "OH", "CA": "RA", "EC": "RA", "SO": "RA", "COMMON_NAME": "Red alder", "PN": "RA"},
        "Corkbark fir": {"WC": "AF", "BM": "AF", "CA": "OS", "EC": "AF", "SO": "OS", "COMMON_NAME": "Corkbark fir", "PN": "AF"},
        "Russian olive": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Russian olive", "PN": "OT"},
        "Catalpa spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Catalpa spp.", "PN": "OT"},
        "Arizona walnut": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Arizona walnut", "PN": "OT"},
        "Cuyamaca cypress": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Cuyamaca cypress", "PN": "OT"},
        "Western juniper": {"WC": "WJ", "BM": "WJ", "CA": "WJ", "EC": "WJ", "SO": "WJ", "COMMON_NAME": "Western juniper", "PN": "WJ"},
        "Brewer spruce": {"WC": "OT", "BM": "OS", "CA": "BR", "EC": "ES", "SO": "ES", "COMMON_NAME": "Brewer spruce", "PN": "OT"},
        "Bigleaf maple": {"WC": "BM", "BM": "OH", "CA": "BM", "EC": "BM", "SO": "BM", "COMMON_NAME": "Bigleaf maple", "PN": "BM"},
        "Rusby's locust": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Rusby's locust", "PN": "OT"},
        "Mesquite spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Mesquite spp.", "PN": "OT"},
        "Yew spp.": {"WC": "PY", "BM": "PY", "CA": "PY", "EC": "PY", "SO": "PY", "COMMON_NAME": "Yew spp.", "PN": "PY"},
        "Parry pinyon": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Parry pinyon", "PN": "OT"},
        "American beech": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "American beech", "PN": "OT"},
        "Blackwood": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Blackwood", "PN": "OT"},
        "Western hemlock": {"WC": "WH", "BM": "GF", "CA": "WH", "EC": "WH", "SO": "WH", "COMMON_NAME": "Western hemlock", "PN": "WH"},
        "Birch spp.": {"WC": "PB", "BM": "OH", "CA": "OH", "EC": "PB", "SO": "OH", "COMMON_NAME": "Birch spp.", "PN": "PB"},
        "Port-Orford-cedar": {"WC": "DF", "BM": "OS", "CA": "PC", "EC": "OS", "SO": "OS", "COMMON_NAME": "Port-Orford-cedar", "PN": "DF"},
        "Blackfruit dogwood": {"WC": "DG", "BM": "OH", "CA": "DG", "EC": "DG", "SO": "OH", "COMMON_NAME": "Blackfruit dogwood", "PN": "DG"},
        "Bank catclaw": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Bank catclaw", "PN": "OT"},
        "Manna gum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Manna gum", "PN": "OT"},
        "Bigelow's willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Bigelow's willow", "PN": "WI"},
        "Apache pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Apache pine", "PN": "OT"},
        "English yew": {"WC": "PY", "BM": "PY", "CA": "PY", "EC": "PY", "SO": "PY", "COMMON_NAME": "English yew", "PN": "PY"},
        "Carolina poplar": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Carolina poplar", "PN": "CW"},
        "Saguaro": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Saguaro", "PN": "OT"},
        "Milfoil wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Milfoil wattle", "PN": "OT"},
        "Santa Cruz Island cypress": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Santa Cruz Island cypress", "PN": "OT"},
        "Valley oak": {"WC": "WO", "BM": "OH", "CA": "VO", "EC": "WO", "SO": "WO", "COMMON_NAME": "Valley oak", "PN": "WO"},
        "Incense cedar": {"WC": "IC", "BM": "OS", "CA": "IC", "EC": "OS", "SO": "IC", "PN": "IC"},
        "Goodding's ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Goodding's ash", "PN": "OT"},
        "Bebb willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Bebb willow", "PN": "WI"},
        "Subalpine larch": {"WC": "LL", "BM": "AF", "CA": "OS", "EC": "LL", "SO": "OS", "COMMON_NAME": "Subalpine larch", "PN": "LL"},
        "Golden wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Golden wattle", "PN": "OT"},
        "Oregon ash": {"WC": "OT", "BM": "OH", "CA": "FL", "EC": "OH", "SO": "OH", "COMMON_NAME": "Oregon ash", "PN": "OT"},
        "Western white pine": {"WC": "WP", "BM": "WP", "CA": "WP", "EC": "WP", "SO": "WP", "COMMON_NAME": "Western white pine", "PN": "WP"},
        "Emory oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Emory oak", "PN": "OT"},
        "White mulberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "White mulberry", "PN": "OT"},
        "Wavyleaf oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Wavyleaf oak", "PN": "OT"},
        "Bigtooth maple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "VN", "SO": "OH", "COMMON_NAME": "Bigtooth maple", "PN": "OT"},
        "Green ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Green ash", "PN": "OT"},
        "Prickly Moses": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Prickly Moses", "PN": "OT"},
        "Black cottonwood": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Black cottonwood", "PN": "CW"},
        "Chinese elm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Chinese elm", "PN": "OT"},
        "Western redcedar": {"WC": "RC", "BM": "GF", "CA": "RC", "EC": "RC", "SO": "RC", "COMMON_NAME": "Western redcedar", "PN": "RC"},
        "Sargent's cypress": {"WC": "OT", "BM": "OS", "CA": "WJ", "EC": "OS", "SO": "OS", "COMMON_NAME": "Sargent's cypress", "PN": "OT"},
        "Hybrid balsam poplar": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Hybrid balsam poplar", "PN": "CW"},
        "Bristly locust": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Bristly locust", "PN": "OT"},
        "Aroeira blanca": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Aroeira blanca", "PN": "OT"},
        "Pinchot's juniper": {"WC": "WJ", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Pinchot's juniper", "PN": "WJ"},
        "Common elderberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Common elderberry", "PN": "OT"},
        "Joshua tree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Joshua tree", "PN": "OT"},
        "Peachleaf willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Peachleaf willow", "PN": "WI"},
        "Eastern cottonwood": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Eastern cottonwood", "PN": "CW"},
        "European alder  ": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "RA", "SO": "OH", "COMMON_NAME": "European alder  ", "PN": "OT"},
        "Mountain alder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "RA", "SO": "OH", "COMMON_NAME": "Mountain alder", "PN": "OT"},
        "Forest redgum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Forest redgum", "PN": "OT"},
        "Madrone spp.": {"WC": "WA", "BM": "OH", "CA": "MA", "EC": "OH", "SO": "OH", "COMMON_NAME": "Madrone spp.", "PN": "WA"},
        "Silver maple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Silver maple", "PN": "OT"},
        "Border pinyon": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Border pinyon", "PN": "OT"},
        "Dogwood spp.": {"WC": "DG", "BM": "OH", "CA": "DG", "EC": "DG", "SO": "OH", "COMMON_NAME": "Dogwood spp.", "PN": "DG"},
        "Fir spp.": {"WC": "SF", "BM": "GF", "CA": "WF", "EC": "GF", "SO": "WF", "COMMON_NAME": "Fir spp.", "PN": "SF"},
        "Tanoak spp.": {"WC": "GC", "BM": "OH", "CA": "TO", "EC": "OH", "SO": "OH", "COMMON_NAME": "Tanoak spp.", "PN": "GC"},
        "American elm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "American elm", "PN": "OT"},
        "Gray alder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "RA", "SO": "OH", "COMMON_NAME": "Gray alder", "PN": "OT"},
        "Arizona boxelder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Arizona boxelder", "PN": "OT"},
        "Cherry": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "CH", "PN": "CH"},
        "Douglas-fir spp.": {"WC": "DF", "BM": "DF", "CA": "DF", "EC": "DF", "SO": "DF", "COMMON_NAME": "Douglas-fir spp.", "PN": "DF"},
        "Mexican flannelbush": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Mexican flannelbush", "PN": "OT"},
        "Japanese angelica tree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Japanese angelica tree", "PN": "OT"},
        "Holly": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Holly", "PN": "OT"},
        "Subalpine fir": {"WC": "AF", "BM": "AF", "CA": "OS", "EC": "AF", "SO": "AF", "COMMON_NAME": "Subalpine fir", "PN": "AF"},
        "Thinleaf alder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "RA", "SO": "OH", "COMMON_NAME": "Thinleaf alder", "PN": "OT"},
        "Punjab fig": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Punjab fig", "PN": "OT"},
        "Western larch": {"WC": "YC", "BM": "WL", "CA": "OS", "EC": "WL", "SO": "WL", "COMMON_NAME": "Western larch", "PN": "YC"},
        "Quaking aspen": {"WC": "AS", "BM": "AS", "CA": "AS", "EC": "AS", "SO": "AS", "COMMON_NAME": "Quaking aspen", "PN": "AS"},
        "Shining willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Shining willow", "PN": "WI"},
        "English holly": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "English holly", "PN": "OT"},
        "Blue oak": {"WC": "WO", "BM": "OH", "CA": "BL", "EC": "WO", "SO": "WO", "COMMON_NAME": "Blue oak", "PN": "WO"},
        "Monterey cypress": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Monterey cypress", "PN": "OT"},
        "Locust": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Locust", "PN": "OT"},
        "Redberry juniper": {"WC": "WJ", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Redberry juniper", "PN": "WJ"},
        "Silktree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Silktree", "PN": "OT"},
        "Tree, evergreen spp.": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Tree, evergreen spp.", "PN": "OT"},
        "Washington fan palm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Washington fan palm", "PN": "OT"},
        "Common pear": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Common pear", "PN": "OT"},
        "Cottonwood": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Cottonwood", "PN": "CW"},
        "Peruvian peppertree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Peruvian peppertree", "PN": "OT"},
        "California-laurel": {"WC": "OT", "BM": "OH", "CA": "CL", "EC": "OH", "SO": "OH", "PN": "OT"},
        "Coastal sage scrub oak": {"WC": "OT", "BM": "OH", "CA": "IO", "EC": "OH", "SO": "OH", "COMMON_NAME": "Coastal sage scrub oak", "PN": "OT"},
        "Giant sequoia": {"WC": "RW", "BM": "OS", "CA": "GS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Giant sequoia", "PN": "RW"},
        "Sugargum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Sugargum", "PN": "OT"},
        "California wax myrtle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "California wax myrtle", "PN": "OT"},
        "English walnut": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "English walnut", "PN": "OT"},
        "Utah juniper": {"WC": "WJ", "BM": "WJ", "CA": "OS", "EC": "WJ", "SO": "WJ", "COMMON_NAME": "Utah juniper", "PN": "WJ"},
        "Strapleaf willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Strapleaf willow", "PN": "WI"},
        "Pallid hoptree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Pallid hoptree", "PN": "OT"},
        "Eastern redcedar": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "WJ", "SO": "OS", "COMMON_NAME": "Eastern redcedar", "PN": "OT"},
        "White ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "White ash", "PN": "OT"},
        "Beaked hazlnut": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "OH", "COMMON_NAME": "Beaked hazlnut", "PN": "CH"},
        "Smallflower tamarisk": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Smallflower tamarisk", "PN": "OT"},
        "Paiute cypress": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Paiute cypress", "PN": "OT"},
        "Unknown softwood": {"WC": "DF", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Unknown softwood", "PN": "DF"},
        "River hawthorn": {"WC": "HT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "River hawthorn", "PN": "HT"},
        "Kenai birch": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Kenai birch", "PN": "OT"},
        "Sitka spruce": {"WC": "ES", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Sitka spruce", "PN": "SS"},
        "Woman's tongue": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Woman's tongue", "PN": "OT"},
        "Golden chain tree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Golden chain tree", "PN": "OT"},
        "Chinese pistache": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Chinese pistache", "PN": "OT"},
        "Italian stone pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Italian stone pine", "PN": "OT"},
        "Sprangletop": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Sprangletop", "PN": "OT"},
        "Catalina ironwood": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Catalina ironwood", "PN": "OT"},
        "Narrowleaf willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Narrowleaf willow", "PN": "WI"},
        "Rocky Mountain Douglas-fir": {"WC": "DF", "BM": "DF", "CA": "DF", "EC": "DF", "SO": "DF", "COMMON_NAME": "Rocky Mountain Douglas-fir", "PN": "DF"},
        "Common hackberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Common hackberry", "PN": "OT"},
        "Great Basin bristlecone pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Great Basin bristlecone pine", "PN": "OT"},
        "Arizona cypress": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Arizona cypress", "PN": "OT"},
        "Buckeye, horsechestnut  ": {"WC": "OT", "BM": "OH", "CA": "BU", "EC": "OH", "SO": "OH", "COMMON_NAME": "Buckeye, horsechestnut  ", "PN": "OT"},
        "Western soapberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Western soapberry", "PN": "OT"},
        "Black wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Black wattle", "PN": "OT"},
        "Tasmanian bluegum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Tasmanian bluegum", "PN": "OT"},
        "Tamarisk spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Tamarisk spp.", "PN": "OT"},
        "Alaska cedar": {"WC": "YC", "BM": "YC", "CA": "PC", "EC": "YC", "SO": "OS", "COMMON_NAME": "Alaska cedar", "PN": "YC"},
        "Boxelder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Boxelder", "PN": "OT"},
        "Rocky Mountain juniper": {"WC": "WJ", "BM": "WJ", "CA": "OS", "EC": "WJ", "SO": "WJ", "COMMON_NAME": "Rocky Mountain juniper", "PN": "WJ"},
        "Pacific silver fir": {"WC": "SF", "BM": "OS", "CA": "SH", "EC": "SF", "SO": "SF", "COMMON_NAME": "Pacific silver fir", "PN": "SF"},
        "Foxtail pine": {"WC": "WB", "BM": "WB", "CA": "WB", "EC": "WB", "SO": "WB", "COMMON_NAME": "Foxtail pine", "PN": "WB"},
        "Desert ironwood  ": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Desert ironwood  ", "PN": "OT"},
        "Bishop pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Bishop pine", "PN": "OT"},
        "Fleshy hawthorn": {"WC": "HT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Fleshy hawthorn", "PN": "HT"},
        "Hophornbeam": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Hophornbeam", "PN": "OT"},
        "Jeffrey pine": {"WC": "JP", "BM": "OS", "CA": "JP", "EC": "PP", "SO": "PP", "COMMON_NAME": "Jeffrey pine", "PN": "JP"},
        "Wingleaf soapberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Wingleaf soapberry", "PN": "OT"},
        "Singleleaf ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Singleleaf ash", "PN": "OT"},
        "Noble fir": {"WC": "NF", "BM": "OS", "CA": "RF", "EC": "NF", "SO": "NF", "COMMON_NAME": "Noble fir", "PN": "NF"},
        "Catclaw acacia": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Catclaw acacia", "PN": "OT"},
        "Monterey pine": {"WC": "OT", "BM": "OS", "CA": "MP", "EC": "OS", "SO": "OS", "COMMON_NAME": "Monterey pine", "PN": "LP"},
        "Gregg's ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Gregg's ash", "PN": "OT"},
        "Bonpland willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Bonpland willow", "PN": "WI"},
        "Tree, deciduous spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Tree, deciduous spp.", "PN": "OT"},
        "California foothill pine": {"WC": "OT", "BM": "OS", "CA": "GP", "EC": "OS", "SO": "OS", "COMMON_NAME": "California foothill pine", "PN": "OT"},
        "Texas walnut  ": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Texas walnut  ", "PN": "OT"},
        "Hackberry spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Hackberry spp.", "PN": "OT"},
        "Incense-cedar": {"WC": "IC", "BM": "OS", "CA": "IC", "EC": "OS", "SO": "IC", "COMMON_NAME": "Incense-cedar", "PN": "IC"},
        "Fremont cottonwood": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Fremont cottonwood", "PN": "CW"},
        "Camphortree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Camphortree", "PN": "OT"},
        "White leadtree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "White leadtree", "PN": "OT"},
        "Gum spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Gum spp.", "PN": "OT"},
        "Velvet mesquite  ": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Velvet mesquite  ", "PN": "OT"},
        "Greene's maple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "VN", "SO": "OH", "COMMON_NAME": "Greene's maple", "PN": "OT"},
        "Horse chestnut": {"WC": "OT", "BM": "OH", "CA": "BU", "EC": "OH", "SO": "OH", "COMMON_NAME": "Horse chestnut", "PN": "OT"},
        "White fir": {"WC": "WF", "BM": "GF", "CA": "WF", "EC": "WF", "SO": "WF", "COMMON_NAME": "White fir", "PN": "WF"},
        "Birchleaf mountain mahogany": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "MB", "COMMON_NAME": "Birchleaf mountain mahogany", "PN": "OT"},
        "Rosewood spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Rosewood spp.", "PN": "OT"},
        "Water birch": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "PB", "SO": "OH", "COMMON_NAME": "Water birch", "PN": "OT"},
        "Arizona pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Arizona pine", "PN": "OT"},
        "Hemlock spp.": {"WC": "WH", "BM": "MH", "CA": "WH", "EC": "WH", "SO": "WH", "COMMON_NAME": "Hemlock spp.", "PN": "WH"},
        "Pacific madrone": {"WC": "WA", "BM": "OH", "CA": "MA", "EC": "OH", "SO": "OH", "COMMON_NAME": "Pacific madrone", "PN": "WA"},
        "Silverleaf mountain gum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Silverleaf mountain gum", "PN": "OT"},
        "Mexican pinyon": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Mexican pinyon", "PN": "OT"},
        "Shreve's prairie acacia": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Shreve's prairie acacia", "PN": "OT"},
        "Red ironbark": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Red ironbark", "PN": "OT"},
        "Gowen cypress": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Gowen cypress", "PN": "OT"},
        "Japanese tree lilac": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Japanese tree lilac", "PN": "OT"},
        "Bristlecone fir": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "WB", "SO": "OS", "COMMON_NAME": "Bristlecone fir", "PN": "OT"},
        "Lodgepole pine": {"WC": "LP", "BM": "LP", "CA": "LP", "EC": "LP", "SO": "LP", "COMMON_NAME": "Lodgepole pine", "PN": "LP"},
        "Oak": {"WC": "WO", "BM": "OH", "CA": "LO", "EC": "WO", "SO": "WO", "COMMON_NAME": "Oak", "PN": "WO"},
        "Siberian elm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Siberian elm", "PN": "OT"},
        "Scotch pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Scotch pine", "PN": "OT"},
        "Cypress spp.": {"WC": "OT", "BM": "WJ", "CA": "WJ", "EC": "WJ", "SO": "WJ", "COMMON_NAME": "Cypress spp.", "PN": "OT"},
        "Willow hawthorn": {"WC": "HT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Willow hawthorn", "PN": "HT"},
        "Giant chinquapin": {"WC": "GC", "BM": "OH", "CA": "GC", "EC": "GC", "SO": "GC", "COMMON_NAME": "Giant chinquapin", "PN": "GC"},
        "Acacia spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Acacia spp.", "PN": "OT"},
        "Western dogwood": {"WC": "DG", "BM": "OH", "CA": "DG", "EC": "DG", "SO": "OH", "COMMON_NAME": "Western dogwood", "PN": "DG"},
        "Hawthorn spp.": {"WC": "HT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Hawthorn spp.", "PN": "HT"},
        "Grand fir": {"WC": "GF", "BM": "GF", "CA": "WF", "EC": "GF", "SO": "GF", "COMMON_NAME": "Grand fir", "PN": "GF"},
        "Southern California walnut": {"WC": "OT", "BM": "OH", "CA": "WN", "EC": "OH", "SO": "OH", "COMMON_NAME": "Southern California walnut", "PN": "OT"},
        "Spikenard": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Spikenard", "PN": "OT"},
        "Sweet crabapple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "OH", "COMMON_NAME": "Sweet crabapple", "PN": "OT"},
        "Shamel ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Shamel ash", "PN": "OT"},
        "Maple spp.": {"WC": "BM", "BM": "OH", "CA": "BM", "EC": "BM", "SO": "BM", "COMMON_NAME": "Maple spp.", "PN": "BM"},
        "Black willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Black willow", "PN": "WI"},
        "Five-stamen tamarisk": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Five-stamen tamarisk", "PN": "OT"},
        "Pygmy cypress": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Pygmy cypress", "PN": "OT"},
        "Walnut spp.": {"WC": "OT", "BM": "OH", "CA": "WN", "EC": "OH", "SO": "OH", "COMMON_NAME": "Walnut spp.", "PN": "OT"},
        "Alderleaf mountain mahogany": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "MB", "COMMON_NAME": "Alderleaf mountain mahogany", "PN": "OT"},
        "Orange wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Orange wattle", "PN": "OT"},
        "Spiny hackberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Spiny hackberry", "PN": "OT"},
        "Elm spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Elm spp.", "PN": "OT"},
        "Balsam poplar": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Balsam poplar", "PN": "CW"},
        "Oak, deciduous spp.": {"WC": "WO", "BM": "OH", "CA": "LO", "EC": "WO", "SO": "WO", "COMMON_NAME": "Oak, deciduous spp.", "PN": "WO"},
        "Gambel oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "WO", "SO": "OH", "COMMON_NAME": "Gambel oak", "PN": "OT"},
        "Interior live oak": {"WC": "WO", "BM": "OH", "CA": "IO", "EC": "OH", "SO": "WO", "COMMON_NAME": "Interior live oak", "PN": "WO"},
        "Balsam willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Balsam willow", "PN": "WI"},
        "Sugar pine": {"WC": "SP", "BM": "OS", "CA": "SP", "EC": "WP", "SO": "SP", "COMMON_NAME": "Sugar pine", "PN": "SP"},
        "Coulter pine": {"WC": "OT", "BM": "OS", "CA": "CP", "EC": "OS", "SO": "OS", "COMMON_NAME": "Coulter pine", "PN": "OT"},
        "Bolander beach pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Bolander beach pine", "PN": "LP"},
        "Lemonscented gum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Lemonscented gum", "PN": "OT"},
        "Deer oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Deer oak", "PN": "OT"},
        "Austrian pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Austrian pine", "PN": "OT"},
        "Curl-leaf mountain mahogany": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "MC", "COMMON_NAME": "Curl-leaf mountain mahogany", "PN": "OT"},
        "White spruce": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "ES", "SO": "OS", "COMMON_NAME": "White spruce", "PN": "OT"},
        "Knobcone pine": {"WC": "KP", "BM": "LP", "CA": "KP", "EC": "LP", "SO": "LP", "COMMON_NAME": "Knobcone pine", "PN": "KP"},
        "Chinaberrytree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Chinaberrytree", "PN": "OT"},
        "California boxelder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "California boxelder", "PN": "OT"},
        "Chihuahuan pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Chihuahuan pine", "PN": "OT"},
        "Leadtree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Leadtree", "PN": "OT"},
        "Aleppo pine": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Aleppo pine", "PN": "OT"},
        "New Mexico locust": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "New Mexico locust", "PN": "OT"},
        "Prairie wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Prairie wattle", "PN": "OT"},
        "Grayleaf willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Grayleaf willow", "PN": "WI"},
        "Oracle oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Oracle oak", "PN": "OT"},
        "Lyononthmnus": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Lyononthmnus", "PN": "OT"},
        "Honeylocust": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Honeylocust", "PN": "OT"},
        "Park willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Park willow", "PN": "WI"},
        "Cyclops acacia": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Cyclops acacia", "PN": "OT"},
        "Tungoil tree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Tungoil tree", "PN": "OT"},
        "Common persimmon": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Common persimmon", "PN": "OT"},
        "Mulberry spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Mulberry spp.", "PN": "OT"},
        "Washoe pine": {"WC": "OT", "BM": "OS", "CA": "PP", "EC": "OS", "SO": "OS", "COMMON_NAME": "Washoe pine", "PN": "OT"},
        "Tamarack": {"WC": "YC", "BM": "WL", "CA": "OS", "EC": "WL", "SO": "WL", "COMMON_NAME": "Tamarack", "PN": "YC"},
        "Bog birch": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Bog birch", "PN": "OT"},
        "Guaje": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Guaje", "PN": "OT"},
        "Shasta red fir": {"WC": "RF", "BM": "OS", "CA": "SH", "EC": "NF", "SO": "SH", "COMMON_NAME": "Shasta red fir", "PN": "RF"},
        "Santa Cruz Island Torrey pine": {"WC": "OT", "BM": "OS", "CA": "MP", "EC": "OS", "SO": "OS", "COMMON_NAME": "Santa Cruz Island Torrey pine", "PN": "OT"},
        "Sydney golden wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Sydney golden wattle", "PN": "OT"},
        "Douglas-fir": {"WC": "DF", "BM": "DF", "CA": "DF", "EC": "DF", "SO": "DF", "COMMON_NAME": "Douglas-fir", "PN": "DF"},
        "Netleaf hackberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Netleaf hackberry", "PN": "OT"},
        "Elaeagnus spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Elaeagnus spp.", "PN": "OT"},
        "Blue spruce": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "ES", "SO": "OS", "COMMON_NAME": "Blue spruce", "PN": "OT"},
        "California black oak": {"WC": "WO", "BM": "OH", "CA": "BO", "EC": "WO", "SO": "WO", "COMMON_NAME": "California black oak", "PN": "WO"},
        "Hemlock": {"WC": "WH", "BM": "MH", "CA": "WH", "EC": "WH", "SO": "WH", "COMMON_NAME": "Hemlock", "PN": "WH"},
        "Melaleuca  ": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Melaleuca  ", "PN": "OT"},
        "Western chokecherry": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "CH", "COMMON_NAME": "Western chokecherry", "PN": "CH"},
        "Redwood": {"WC": "RW", "BM": "OS", "CA": "GS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Redwood", "PN": "RW"},
        "California live oak": {"WC": "WO", "BM": "OH", "CA": "LO", "EC": "WO", "SO": "WO", "COMMON_NAME": "California live oak", "PN": "WO"},
        "Plains cottonwood": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "Plains cottonwood", "PN": "CW"},
        "MacNab's cypress": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "MacNab's cypress", "PN": "OT"},
        "Alligator juniper": {"WC": "WJ", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Alligator juniper", "PN": "WJ"},
        "Beech spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Beech spp.", "PN": "OT"},
        "European beech": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "European beech", "PN": "OT"},
        "Water wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Water wattle", "PN": "OT"},
        "California laurel": {"WC": "OT", "BM": "OH", "CA": "CL", "EC": "OH", "SO": "OH", "COMMON_NAME": "California laurel", "PN": "OT"},
        "Canyon live oak": {"WC": "WO", "BM": "OH", "CA": "CY", "EC": "OH", "SO": "WO", "COMMON_NAME": "Canyon live oak", "PN": "WO"},
        "Oneseed juniper": {"WC": "WJ", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Oneseed juniper", "PN": "WJ"},
        "Cascara buckthorn": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "OH", "COMMON_NAME": "Cascara buckthorn", "PN": "CH"},
        "Paper birch": {"WC": "PB", "BM": "OH", "CA": "OH", "EC": "PB", "SO": "OH", "COMMON_NAME": "Paper birch", "PN": "PB"},
        "Redosier dogwood": {"WC": "DG", "BM": "OH", "CA": "DG", "EC": "DG", "SO": "OH", "COMMON_NAME": "Redosier dogwood", "PN": "DG"},
        "Canary Island date palm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Canary Island date palm", "PN": "OT"},
        "Littleleaf mountain mahogany": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "MB", "COMMON_NAME": "Littleleaf mountain mahogany", "PN": "OT"},
        "McCalla's willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "McCalla's willow", "PN": "WI"},
        "Chihuahuan ash": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Chihuahuan ash", "PN": "OT"},
        "Chinese tallow": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Chinese tallow", "PN": "OT"},
        "Yewleaf willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Yewleaf willow", "PN": "WI"},
        "Elderberry spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Elderberry spp.", "PN": "OT"},
        "Saltcedar": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Saltcedar", "PN": "OT"},
        "Ohio buckeye  ": {"WC": "OT", "BM": "OH", "CA": "BU", "EC": "OH", "SO": "OH", "COMMON_NAME": "Ohio buckeye  ", "PN": "OT"},
        "Cedar wattle": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Cedar wattle", "PN": "OT"},
        "Tecate cypress": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Tecate cypress", "PN": "OT"},
        "Whitethorn acacia": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Whitethorn acacia", "PN": "OT"},
        "European white birch": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "European white birch", "PN": "OT"},
        "Pine spp.": {"WC": "LP", "BM": "PP", "CA": "SP", "EC": "LP", "SO": "PP", "COMMON_NAME": "Pine spp.", "PN": "LP"},
        "Toumey oak": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Toumey oak", "PN": "OT"},
        "River redgum": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "River redgum", "PN": "OT"},
        "Black locust": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Black locust", "PN": "OT"},
        "Jaeger's Joshua tree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Jaeger's Joshua tree", "PN": "OT"},
        "Sierra lodgepole pine": {"WC": "LP", "BM": "LP", "CA": "LP", "EC": "LP", "SO": "LP", "COMMON_NAME": "Sierra lodgepole pine", "PN": "LP"},
        "St. John's bread": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "St. John's bread", "PN": "OT"},
        "Date palm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Date palm", "PN": "OT"},
        "Ash spp.": {"WC": "OT", "BM": "OH", "CA": "FL", "EC": "OH", "SO": "OH", "COMMON_NAME": "Ash spp.", "PN": "OT"},
        "Northern California walnut": {"WC": "OT", "BM": "OH", "CA": "WN", "EC": "OH", "SO": "OH", "COMMON_NAME": "Northern California walnut", "PN": "OT"},
        "Tree of heaven": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Tree of heaven", "PN": "OT"},
        "Arizona madrone": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Arizona madrone", "PN": "OT"},
        "Hoptree spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Hoptree spp.", "PN": "OT"},
        "Scouler's willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Scouler's willow", "PN": "WI"},
        "Locust spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Locust spp.", "PN": "OT"},
        "Chokecherry": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "CH", "COMMON_NAME": "Chokecherry", "PN": "CH"},
        "Texas mulberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Texas mulberry", "PN": "OT"},
        "Singleleaf pinyon": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "OS", "SO": "OS", "COMMON_NAME": "Singleleaf pinyon", "PN": "OT"},
        "Cerro hawthorn": {"WC": "HT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Cerro hawthorn", "PN": "HT"},
        "Arizona rosewood": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Arizona rosewood", "PN": "OT"},
        "Dwarf birch": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "PB", "SO": "OH", "COMMON_NAME": "Dwarf birch", "PN": "OT"},
        "Soapberry spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Soapberry spp.", "PN": "OT"},
        "Texan sugarberry": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Texan sugarberry", "PN": "OT"},
        "Brazilian peppertree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Brazilian peppertree", "PN": "OT"},
        "Goodding's willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Goodding's willow", "PN": "WI"},
        "Tanoak": {"WC": "GC", "BM": "OH", "CA": "TO", "EC": "OH", "SO": "OH", "COMMON_NAME": "Tanoak", "PN": "GC"},
        "Northern catalpa": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Northern catalpa", "PN": "OT"},
        "Bitter cherry": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "CH", "COMMON_NAME": "Bitter cherry", "PN": "CH"},
        "White poplar": {"WC": "CW", "BM": "CW", "CA": "CW", "EC": "CW", "SO": "CW", "COMMON_NAME": "White poplar", "PN": "CW"},
        "Loquat": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Loquat", "PN": "OT"},
        "Torrey pine": {"WC": "OT", "BM": "OS", "CA": "MP", "EC": "OS", "SO": "OS", "COMMON_NAME": "Torrey pine", "PN": "OT"},
        "Cabbage tree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Cabbage tree", "PN": "OT"},
        "White willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "White willow", "PN": "WI"},
        "Hardee peppertree": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Hardee peppertree", "PN": "OT"},
        "Green alder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "RA", "SO": "OH", "COMMON_NAME": "Green alder", "PN": "OT"},
        "Sitka alder": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "RA", "SO": "OH", "COMMON_NAME": "Sitka alder", "PN": "OT"},
        "Amur lilac": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Amur lilac", "PN": "OT"},
        "Lacebark": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Lacebark", "PN": "OT"},
        "Lutz's spruce": {"WC": "OT", "BM": "OS", "CA": "OS", "EC": "ES", "SO": "OS", "COMMON_NAME": "Lutz's spruce", "PN": "OT"},
        "Canyon maple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "VN", "SO": "OH", "COMMON_NAME": "Canyon maple", "PN": "OT"},
        "New Mexico maple": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "VN", "SO": "OH", "COMMON_NAME": "New Mexico maple", "PN": "OT"},
        "Wych elm": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Wych elm", "PN": "OT"},
        "Diamondleaf willow": {"WC": "WI", "BM": "OH", "CA": "WI", "EC": "WI", "SO": "WI", "COMMON_NAME": "Diamondleaf willow", "PN": "WI"},
        "Cedar spp.": {"WC": "YC", "BM": "YC", "CA": "PC", "EC": "YC", "SO": "OS", "COMMON_NAME": "Cedar spp.", "PN": "YC"},
        "Fig spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Fig spp.", "PN": "OT"},
        "Common lilac": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Common lilac", "PN": "OT"},
        "California red fir": {"WC": "RF", "BM": "OS", "CA": "RF", "EC": "NF", "SO": "SH", "COMMON_NAME": "California red fir", "PN": "RF"},
        "Hophornbean spp.": {"WC": "OT", "BM": "OH", "CA": "OH", "EC": "OH", "SO": "OH", "COMMON_NAME": "Hophornbean spp.", "PN": "OT"},
        "American plum": {"WC": "CH", "BM": "OH", "CA": "OH", "EC": "PL", "SO": "CH", "COMMON_NAME": "American plum", "PN": "CH"}
    }

    # For each species_mindbh_maxdbh...
    # "sc": "Species Class"?
    for sc in stand_list:

        if settings.USE_FIA_NN_MATCHING:
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
        else:
            sql = """
                SELECT
                    treelive_summary.COND_ID,
                    SUM(SumOfTPA) as "TPA__",
                    SUM(SumOfBA_FT2_AC) as "BAA__",
                    SUM(pct_of_totalba) as "PCTBA__",
                    AVG(COUNT_SPECIESSIZECLASSES) as "PLOTCLASSCOUNT__",
                    AVG(TOTAL_BA_FT2_AC) as "PLOTBA__"
                FROM treelive_summary, trees_conditionvariantlookup as cvl
                WHERE fvs_spp_code = %(fvsspecies)s
                AND variant = %(variant_code)s
                AND cvl.cond_id = treelive_summary.cond_id  --join
                AND cvl.variant_code = %(variant_code)s
                AND calc_dbh_class >= %(lowsize)s AND calc_dbh_class < %(highsize)s
                AND pct_of_totalba is not null
                GROUP BY treelive_summary.COND_ID
            """
        inputs = {
            'species': sc[0],
            'fvsspecies': common_species_lookup[sc[0]][variant],
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


        # df is condition ids that match sql query of each (single species + dbh range)
        df = pd.DataFrame(rows)
        df.index = df['cond_id']
        del df['cond_id']
        #dfs is collection of df lists of cond ids
        dfs.append(df)

    if len(dfs) == 0:
        raise NearestNeighborError("The stand list provided does not yield enough matches.")
    elif len(dfs) == 1:
        sdfs = dfs
    else:
        #sdfs is queries sorted by number of matches (species + dbh-range) returned
        sdfs = sorted(dfs, key=lambda x: len(x), reverse=True)

    enough = False
    while not enough:
        if len(sdfs) == 0:
            raise NearestNeighborError("The stand list provided does not yield enough matches.")
        #cadidates are cond_ids with all (species + dbh range) represented
        candidates = pd.concat(sdfs, axis=1, join="inner")
        if verbose:
            print(len(candidates))
        if len(candidates) < min_candidates:
            aa = sdfs.pop()  # remove the one with smallest number
            if verbose:
                print("Popping", [x.replace("BAA_", "")
                                  for x in aa.columns.tolist()
                                  if x.startswith('BAA_')][0])

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
        print("----- estimated total basal area", total_ba)

    # query for candidates
    candidates = get_candidates(stand_list, variant, verbose=verbose)

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
            'TOTAL_PCTBA': 1.0,
            'PLOT_BA': 15.0,
            'NONSPEC_BA': 5.0,
            'NONSPEC_TPA': 0.1,
            'TOTAL_TPA': 0.1,
            'stand_age': 20.0,
            'calc_slope': 0.1,
            'calc_aspect': 1.0,
            'elev_ft': 1.0,
            'latitude_fuzz': 1.0,
            'longitude_fuzz': 1.0,
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
        elif key.startswith("BAA_"):
            weights[i] = 1.5
        elif key.startswith("TPA_"):
            weights[i] = 1.0

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
            # Pandas deprecated irow in favor of iloc instead:
            # http://pandas.pydata.org/pandas-docs/version/0.19.2/generated/pandas.DataFrame.irow.html
            pseries = plotsummaries.iloc[t[0]]
            if verbose:
                sp = [round(x, 2) for x in list(scaled_points[t[0]])]
                table_data.append((sp, 'scaled/weighted candidate %s' % pseries.name))
        except IndexError:
            continue

        # certainty of 0 -> distance is furthest possible
        # certainty of 1 -> the point matches exactly
        # sqrt of ratio taken to exagerate small diffs

        # set_value is also deprecated in pandas
        # pseries = pseries.set_value('_kdtree_distance', t[1])
        pseries.loc['_kdtree_distance'] = t[1]
        # pseries = pseries.set_value('_certainty', 1.0 - ((t[1] / max_dist) ** 0.5))
        pseries.loc['_certainty'] = 1.0 - ((t[1] / max_dist) ** 0.5)

        ps.append(pseries)

    if verbose:
        print("".join(["%-32s" % ("| " + x) for x in headers[::4]]))
        print(" "*8 + "".join(["%-32s" % ("| " + x) for x in headers[1::4]]))
        print(" "*16 + "".join(["%-32s" % ("| " + x) for x in headers[2::4]]))
        print(" "*24 + "".join(["%-32s" % ("| " + x) for x in headers[3::4]]))
        print("|-------" * (len(headers) + 1))

        for td in table_data:
            print("".join(["%8s" % str(x) for x in td[0]]), td[1])

    return ps, num_candidates
