# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Parcel.apn'
        db.alter_column('trees_parcel', 'apn', self.gf('django.db.models.fields.CharField')(max_length=40))


    def backwards(self, orm):
        
        # Changing field 'Parcel.apn'
        db.alter_column('trees_parcel', 'apn', self.gf('django.db.models.fields.IntegerField')())


    models = {
        'trees.parcel': {
            'Meta': {'object_name': 'Parcel'},
            'apn': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3857'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'trees.streambuffer': {
            'Meta': {'object_name': 'StreamBuffer'},
            'area': ('django.db.models.fields.FloatField', [], {}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3857'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inside': ('django.db.models.fields.IntegerField', [], {}),
            'perimeter': ('django.db.models.fields.FloatField', [], {}),
            'str_buf_field': ('django.db.models.fields.IntegerField', [], {}),
            'str_buf_id': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['trees']
