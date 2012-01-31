from django.contrib.gis.db import models
from django.contrib.gis.utils import LayerMapping
import os

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

class Stand(models.Model):
    geom = models.MultiPolygonField(srid=3857)
    objects = models.GeoManager()

stand_mapping = {
    'geom': 'MULTIPOLYGON'
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
    #stands_shp = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/sixes/elliot_stands_3857.shp'))
    for s in Stand.objects.all():
        s.delete()
    map1 = LayerMapping(Stand, stands_shp, stand_mapping, transform=False, encoding='iso-8859-1')
    map1.save(strict=True, verbose=True)
