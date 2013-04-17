# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Rx'
        db.create_table('trees_rx', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('variant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trees.FVSVariant'])),
            ('internal_name', self.gf('django.db.models.fields.TextField')()),
            ('internal_desc', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('trees', ['Rx'])

        # Adding model 'ScenarioStand'
        db.create_table('trees_scenariostand', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='trees_scenariostand_related', to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length='255')),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='trees_scenariostand_related', null=True, to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('manipulators', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('geometry_orig', self.gf('django.contrib.gis.db.models.fields.PolygonField')(srid=3857, null=True, blank=True)),
            ('geometry_final', self.gf('django.contrib.gis.db.models.fields.PolygonField')(srid=3857, null=True, blank=True)),
            ('cond_id', self.gf('django.db.models.fields.BigIntegerField')()),
            ('rx', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trees.Rx'], null=True)),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trees.Scenario'])),
            ('stand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trees.Stand'])),
            ('constraint', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trees.SpatialConstraint'])),
        ))
        db.send_create_signal('trees', ['ScenarioStand'])

        # Adding M2M table for field sharing_groups on 'ScenarioStand'
        db.create_table('trees_scenariostand_sharing_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('scenariostand', models.ForeignKey(orm['trees.scenariostand'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('trees_scenariostand_sharing_groups', ['scenariostand_id', 'group_id'])

        # Adding model 'MyRx'
        db.create_table('trees_myrx', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='trees_myrx_related', to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length='255')),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='trees_myrx_related', null=True, to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('rx', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trees.Rx'])),
        ))
        db.send_create_signal('trees', ['MyRx'])

        # Adding M2M table for field sharing_groups on 'MyRx'
        db.create_table('trees_myrx_sharing_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('myrx', models.ForeignKey(orm['trees.myrx'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('trees_myrx_sharing_groups', ['myrx_id', 'group_id'])

        # Adding model 'SpatialConstraint'
        db.create_table('trees_spatialconstraint', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')(srid=3857)),
            ('default_rx', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trees.Rx'])),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=2)),
        ))
        db.send_create_signal('trees', ['SpatialConstraint'])

        # Adding field 'FVSVariant.decision_tree_xml'
        db.add_column('trees_fvsvariant', 'decision_tree_xml',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Scenario.spatial_constraints'
        db.add_column('trees_scenario', 'spatial_constraints',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Rx'
        db.delete_table('trees_rx')

        # Deleting model 'ScenarioStand'
        db.delete_table('trees_scenariostand')

        # Removing M2M table for field sharing_groups on 'ScenarioStand'
        db.delete_table('trees_scenariostand_sharing_groups')

        # Deleting model 'MyRx'
        db.delete_table('trees_myrx')

        # Removing M2M table for field sharing_groups on 'MyRx'
        db.delete_table('trees_myrx_sharing_groups')

        # Deleting model 'SpatialConstraint'
        db.delete_table('trees_spatialconstraint')

        # Deleting field 'FVSVariant.decision_tree_xml'
        db.delete_column('trees_fvsvariant', 'decision_tree_xml')

        # Deleting field 'Scenario.spatial_constraints'
        db.delete_column('trees_scenario', 'spatial_constraints')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'trees.county': {
            'Meta': {'object_name': 'County'},
            'cnty_fips': ('django.db.models.fields.IntegerField', [], {}),
            'cntyname': ('django.db.models.fields.CharField', [], {'max_length': '23'}),
            'fips': ('django.db.models.fields.IntegerField', [], {}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3857'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polytype': ('django.db.models.fields.IntegerField', [], {}),
            'soc_cnty': ('django.db.models.fields.IntegerField', [], {}),
            'st_fips': ('django.db.models.fields.IntegerField', [], {}),
            'stname': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'trees.forestproperty': {
            'Meta': {'object_name': 'ForestProperty'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'trees_forestproperty_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'geometry_final': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3857', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'trees_forestproperty_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'trees_forestproperty_related'", 'to': "orm['auth.User']"})
        },
        'trees.fvsspecies': {
            'AK': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'BM': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'CA': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'CI': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'CR': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'EC': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'EM': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'IE': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'KT': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'Meta': {'object_name': 'FVSSpecies'},
            'NC': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'NI': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'PN': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'SO': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'TT': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'UT': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'WC': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'WS': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'common': ('django.db.models.fields.TextField', [], {}),
            'fia': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'fvs': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scientific': ('django.db.models.fields.TextField', [], {}),
            'usda': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'})
        },
        'trees.fvsvariant': {
            'Meta': {'object_name': 'FVSVariant'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'decision_tree_xml': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'fvsvariant': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3857'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'trees.idbsummary': {
            'Meta': {'object_name': 'IdbSummary', 'db_table': "u'idb_summary'"},
            'acres': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'acres_vol': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'age_dom': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'aspect_deg': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'avgofba_ft2_ac': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'avgofdbh_in': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'avgofht_ft': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'avgofslope': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'avgoftpa': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'baa_ge_3': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'baa_ge_3_stunits': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'bac_ge_3': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'bac_prop': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'bah_ge_3': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'calc_aspect': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'calc_slope': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'cancov': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'cond_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'countofsubplot_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'county_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'covcl': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'elev_ft': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fia_forest_type_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'firstofaspect_deg': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'for_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'for_type_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'for_type_secdry': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'for_type_secdry_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'forest_name': ('django.db.models.fields.CharField', [], {'max_length': '510', 'null': 'True', 'blank': 'True'}),
            'fvs_variant': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'halfstate_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'latitude_fuzz': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'longitude_fuzz': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mai': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'ogsi': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'own_group': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'plant_assoc_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'plot_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'qmd_hwd_cm': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'qmd_swd_cm': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'qmd_tot_cm': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'qmda_dom': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'qmda_dom_stunits': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'qmdc_dom': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'qmdh_dom': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'sdi': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'sdi_reineke': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'site_class_fia': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'site_index_fia': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'site_species': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sizecl': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slope': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'stand_age': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'stand_age_even_yn': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'stand_size_class': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'stdevofaspect_deg': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'stdevofslope': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'stndhgt': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'stndhgt_stunits': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'struccond': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'struccondr': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sumofba_ft2': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'tph_ge_3': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'tph_ge_3_stunits': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'vegclass': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'vegclassr': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'trees.myrx': {
            'Meta': {'object_name': 'MyRx'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'trees_myrx_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rx': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trees.Rx']"}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'trees_myrx_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'trees_myrx_related'", 'to': "orm['auth.User']"})
        },
        'trees.rx': {
            'Meta': {'object_name': 'Rx'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal_desc': ('django.db.models.fields.TextField', [], {}),
            'internal_name': ('django.db.models.fields.TextField', [], {}),
            'variant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trees.FVSVariant']"})
        },
        'trees.scenario': {
            'Meta': {'object_name': 'Scenario'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'trees_scenario_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_age_class': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'input_property': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trees.ForestProperty']"}),
            'input_rxs': ('trees.models.JSONField', [], {'default': "'{}'", 'null': 'True', 'blank': 'True'}),
            'input_target_boardfeet': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'input_target_carbon': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'output_scheduler_results': ('trees.models.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'trees_scenario_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'spatial_constraints': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'trees_scenario_related'", 'to': "orm['auth.User']"})
        },
        'trees.scenariostand': {
            'Meta': {'object_name': 'ScenarioStand'},
            'cond_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'constraint': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trees.SpatialConstraint']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'trees_scenariostand_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'geometry_final': ('django.contrib.gis.db.models.fields.PolygonField', [], {'srid': '3857', 'null': 'True', 'blank': 'True'}),
            'geometry_orig': ('django.contrib.gis.db.models.fields.PolygonField', [], {'srid': '3857', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manipulators': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rx': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trees.Rx']", 'null': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trees.Scenario']"}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'trees_scenariostand_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'stand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trees.Stand']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'trees_scenariostand_related'", 'to': "orm['auth.User']"})
        },
        'trees.spatialconstraint': {
            'Meta': {'object_name': 'SpatialConstraint'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'default_rx': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trees.Rx']"}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {'srid': '3857'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'trees.stand': {
            'Meta': {'object_name': 'Stand'},
            'aspect': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'cond_id': ('django.db.models.fields.BigIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'trees_stand_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'cost': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'elevation': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'geometry_final': ('django.contrib.gis.db.models.fields.PolygonField', [], {'srid': '3857', 'null': 'True', 'blank': 'True'}),
            'geometry_orig': ('django.contrib.gis.db.models.fields.PolygonField', [], {'srid': '3857', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manipulators': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'nn_savetime': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rast_savetime': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'trees_stand_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'slope': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'strata': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['trees.Strata']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'trees_stand_related'", 'to': "orm['auth.User']"})
        },
        'trees.strata': {
            'Meta': {'object_name': 'Strata'},
            'additional_desc': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'trees_strata_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'search_age': ('django.db.models.fields.FloatField', [], {}),
            'search_tpa': ('django.db.models.fields.FloatField', [], {}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'trees_strata_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'stand_list': ('trees.models.JSONField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'trees_strata_related'", 'to': "orm['auth.User']"})
        },
        'trees.treelivesummary': {
            'Meta': {'object_name': 'TreeliveSummary', 'db_table': "u'treelive_summary'"},
            'avgofage_bh': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'avgofba_ft2_ac': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'avgofdbh_in': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'avgofht_ft': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'avgoftpa': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'calc_dbh_class': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'calc_tree_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'class_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'cond_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'count_speciessizeclasses': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fia_forest_type_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'pct_of_totalba': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'plot_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sumofba_ft2_ac': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'sumoftpa': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'total_ba_ft2_ac': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'varname': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'})
        }
    }

    complete_apps = ['trees']