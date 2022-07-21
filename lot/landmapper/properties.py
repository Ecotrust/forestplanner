from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.cache import cache
from landmapper.models import Taxlot, Property, PropertyRecord
from landmapper import reports
from urllib.parse import unquote

def create_property(taxlot_ids, property_name, user=None):
    # '''
    # Land Mapper: Create Property
    #
    # TODO:
    #     can a memory instance of feature be made as opposed to a database feature
    #         meta of model (ref: madrona.features) to be inherited?
    #         don't want this in a database
    #         use a class (python class) as opposed to django model class?
    #     add methods to class for
    #         creating property
    #         turn into shp
    #         CreatePDF, ExportLayer, BuildLegend, BuildTables?
    #     research caching approaches
    #         django docs
    #         django caching API
    # '''
    '''
    (called before loading 'Report', cached)
    IN:
        taxlot_ids[ ]
        property_name
    OUT:
        Madrona polygon feature
    NOTES:
        CACHE THESE!!!!
    '''

    if user.is_anonymous:
        user = None

    taxlot_multipolygon = False

    taxlots = Taxlot.objects.filter(pk__in=taxlot_ids)

    for lot in taxlots:
        # lot = Taxlot.objects.get(pk=lot_id)
        if not taxlot_multipolygon:
            taxlot_multipolygon = lot.geometry
        else:
            taxlot_multipolygon = taxlot_multipolygon.union(lot.geometry)

    # Create Property object (don't use 'objects.create()'!)
    # now create property from cache id on report page
    if type(taxlot_multipolygon) == Polygon:
        taxlot_multipolygon = MultiPolygon(taxlot_multipolygon)

    property_record, created = PropertyRecord.objects.get_or_create(user=user,
                        geometry_orig=taxlot_multipolygon,
                        name=property_name)

    property_record.taxlots_json = {'taxlots': taxlot_ids}
    property_record.save()

    property = Property(
                        pk=property_record.pk,
                        user=user,
                        geometry_orig=taxlot_multipolygon,
                        name=property_name)

    reports.get_property_report(property, taxlots)

    return property

def get_property_by_id(property_id, user=None):
    property = cache.get('%s' % property_id)

    if not property:
        id_elements = property_id.split('|')
        # Url Decode property's name
        property = create_property(id_elements[1:], unquote(id_elements[0]), user)
        # Cache for 1 week
        cache.set('%s' % property_id, property, 60 * 60 * 24 * 7)

    return property
