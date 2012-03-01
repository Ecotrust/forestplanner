import os
from django.contrib.gis.db import models
from django.contrib.gis.utils import LayerMapping
from django.core.exceptions import ValidationError
from django.utils.simplejson import dumps
from madrona.features.models import PolygonFeature, FeatureCollection
from madrona.features import register, alternate

@register
class Stand(PolygonFeature):
    RX_CHOICES = (
        ('CC', 'Clearcut'),
        ('SW', 'Shelterwood'),
    )
    SPP_CHOICES = (
        ('DF', 'Douglas Fir'),
        ('MH', 'Mountain Hemlock'),
    )
    rx = models.CharField(max_length=2, choices=RX_CHOICES, 
            verbose_name="Presciption", default="CC")
    domspp = models.CharField(max_length=2, choices=SPP_CHOICES, 
            verbose_name="Dominant Species", default="DF")

    class Options:
        form = "lot.trees.forms.StandForm"
        links = (
            alternate('GeoJSON',
                'trees.views.json_featurecollection',  
                type="application/json",
                select='multiple single'),
        )

    @property
    def geojson(self):
        d = {
             'uid': self.uid,
             'name': self.name,
             'date_modified': str(self.date_modified),
             'rx': self.get_rx_display(),
             'domspp': self.get_domspp_display()
        }

        j = """
            { 
              "type": "Feature",
              "geometry": %s,
              "properties": %s 
            }""" % (self.geometry_final.json, dumps(d))

        return j

@register
class ForestProperty(FeatureCollection):
    class Options:
        valid_children = ('lot.trees.models.Stand',)
        form = "lot.trees.forms.PropertyForm"

class Parcel(models.Model):
    apn = models.CharField(max_length=40)
    geom = models.MultiPolygonField(srid=3857)
    objects = models.GeoManager()

class StreamBuffer(models.Model):
    area = models.FloatField()
    perimeter = models.FloatField()
    str_buf_field = models.IntegerField()
    str_buf_id = models.IntegerField()
    inside = models.IntegerField()
    geom = models.MultiPolygonField(srid=3857)
    objects = models.GeoManager()

stand_mapping = {
    'name': 'STAND_TEXT',
    'geometry_final': 'POLYGON',
    'geometry_original': 'POLYGON'
}

# Auto-generated `LayerMapping` dictionary for Parcel model
parcel_mapping = {
    'apn' : 'APN',
    'geom' : 'MULTIPOLYGON',
}

# Auto-generated `LayerMapping` dictionary for StreamBuffer model
streambuffer_mapping = {
    'area' : 'AREA',
    'perimeter' : 'PERIMETER',
    'str_buf_field' : 'STR_BUF_',
    'str_buf_id' : 'STR_BUF_ID',
    'inside' : 'INSIDE',
    'geom' : 'MULTIPOLYGON',
}

def run():
    verbose = True

    parcel_shp = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/landowner_demo/merc/Parcels.shp'))
    for p in Parcel.objects.all():
        p.delete()
    map1 = LayerMapping(Parcel, parcel_shp, parcel_mapping, transform=False, encoding='iso-8859-1')
    map1.save(strict=True, verbose=verbose)

    streambuffer_shp = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/landowner_demo/merc/stream_buffer_clip.shp'))
    for sb in StreamBuffer.objects.all():
        sb.delete()
    map2 = LayerMapping(StreamBuffer, streambuffer_shp, streambuffer_mapping, transform=False, encoding='iso-8859-1')
    map2.save(strict=True, verbose=verbose)

def import_stands():
    stands_shp = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/sixes/sixes_stands_3857b.shp'))
    for s in Stand.objects.all():
        s.delete()
    map1 = LayerMapping(Stand, stands_shp, stand_mapping, transform=False, encoding='iso-8859-1')
    map1.save(strict=True, verbose=True)
