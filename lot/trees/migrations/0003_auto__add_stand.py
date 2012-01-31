# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Stand'
        db.create_table('trees_stand', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(srid=3857)),
        ))
        db.send_create_signal('trees', ['Stand'])


    def backwards(self, orm):
        
        # Deleting model 'Stand'
        db.delete_table('trees_stand')


    models = {
        'trees.parcel': {
            'Meta': {'object_name': 'Parcel'},
            'apn': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3857'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'trees.stand': {
            'Meta': {'object_name': 'Stand'},
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
