# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Parcel'
        db.create_table('trees_parcel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('apn', self.gf('django.db.models.fields.IntegerField')()),
            ('geom', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(srid=3857)),
        ))
        db.send_create_signal('trees', ['Parcel'])

        # Adding model 'StreamBuffer'
        db.create_table('trees_streambuffer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('django.db.models.fields.FloatField')()),
            ('perimeter', self.gf('django.db.models.fields.FloatField')()),
            ('str_buf_field', self.gf('django.db.models.fields.IntegerField')()),
            ('str_buf_id', self.gf('django.db.models.fields.IntegerField')()),
            ('inside', self.gf('django.db.models.fields.IntegerField')()),
            ('geom', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(srid=3857)),
        ))
        db.send_create_signal('trees', ['StreamBuffer'])


    def backwards(self, orm):
        
        # Deleting model 'Parcel'
        db.delete_table('trees_parcel')

        # Deleting model 'StreamBuffer'
        db.delete_table('trees_streambuffer')


    models = {
        'trees.parcel': {
            'Meta': {'object_name': 'Parcel'},
            'apn': ('django.db.models.fields.IntegerField', [], {}),
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
