# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'TreeliveSummary', fields ['cond_id']
        db.delete_unique(u'treelive_summary', ['cond_id'])

        # Deleting model 'PlotSummary'
        db.delete_table(u'sppsz_attr_all')

        # Deleting model 'GNN_ORWA'
        db.delete_table('trees_gnn_orwa')

        # Deleting model 'Parcel'
        db.delete_table('trees_parcel')

        # Deleting model 'StreamBuffer'
        db.delete_table('trees_streambuffer')

        # Deleting model 'TreeLive'
        db.delete_table(u'tree_live')

        # Deleting model 'PlotLookup'
        db.delete_table('trees_plotlookup')

        # Adding field 'TreeliveSummary.class_id'
        db.add_column(u'treelive_summary', 'class_id', self.gf('django.db.models.fields.BigIntegerField')(default=1, primary_key=True), keep_default=False)

        # Adding field 'TreeliveSummary.varname'
        db.add_column(u'treelive_summary', 'varname', self.gf('django.db.models.fields.CharField')(default='', max_length=60, blank=True), keep_default=False)

        # Changing field 'TreeliveSummary.cond_id'
        db.alter_column(u'treelive_summary', 'cond_id', self.gf('django.db.models.fields.BigIntegerField')(null=True))


    def backwards(self, orm):
        
        # Adding model 'PlotSummary'
        db.create_table(u'sppsz_attr_all', (
            ('tph_rems', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tphc_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vegclassr', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('fortypba', self.gf('django.db.models.fields.CharField')(max_length=42, null=True, blank=True)),
            ('rem_pctl', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('cancov_hdw', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('qmdc_75pct', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('svph_ge_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('iv_con', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('stph_ge_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tphtol_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tphintol_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bac_75_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('qmdc_dom', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bah_50_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vph_reml', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bac_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('baa_25_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('plot', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('vph_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dvph_25_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bah_3_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tphc_ge_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('imap_domspp', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('stph_ge_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('vphc_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('sdi', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tph_3_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('imap_qmd', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dvph_50_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('sddbh', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('stph_ge_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('occasion_num', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('covcl', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('dvph_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dvph_ge_12', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dcov_ge_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dvph_ge_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('ogsi', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bac_25_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tph_75_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('svph_75_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('map_source', self.gf('django.db.models.fields.CharField')(max_length=8, null=True, blank=True)),
            ('cancov_dom', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('stph_ge_12', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('age_dom_no_rem', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vc_qmdc', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('sbph_5_9_in', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('assessment_year', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('sdba', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('eslf_name', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('cnty', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('dcov_12_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('data_source', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('tphh_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('fortypcov', self.gf('django.db.models.fields.CharField')(max_length=42, null=True, blank=True)),
            ('idb_plot_id', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('rem_pctd', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vph_rems', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('fortypiv', self.gf('django.db.models.fields.CharField')(max_length=42, null=True, blank=True)),
            ('fcid', self.gf('django.db.models.fields.BigIntegerField')(unique=True, primary_key=True)),
            ('vphh_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('stph_25_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('qmdh_dom', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('cancov', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('sbph_9_20_in', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bac_prop', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('svph_ge_12', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('uplcov', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('rem_pcts', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vc_qmda', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('conr', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('vph_25_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dvph_12_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('lsog_tphc_50', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('bah_prop', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tph_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('svph_ge_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('qmda_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('qmdc_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('baa_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dcov_ge_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('mndbhba_hdw', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tph_50_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('stndhgt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bac_3_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('iv_hdw', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bah_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('hdwr', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('conplba', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('tph_reml', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tphc_ge_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('hdwpliv', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('sbph_ge_12', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('imap_layers', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('mndbhba_con', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vph_3_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('half_state', self.gf('django.db.models.fields.CharField')(max_length=6, null=True, blank=True)),
            ('mndbhba_all', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('sdi_reineke', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('hcb', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('svph_25_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('ddi', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bac_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bah_25_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('baa_75_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dcov_ge_12', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dcov_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('hdwplcov', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('dcov_25_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('treer', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('sizecl', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('qmda_dom', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('qmdh_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('stph_12_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('svph_ge_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tphc_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('svph_12_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tph_25_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dvph_ge_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dcov_ge_50', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('struccond', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('dcov_50_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('conplcov', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('baa_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('age_dom', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('sc', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('vph_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('baa_50_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bph_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('stph_50_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('stph_75_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vph_75_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('baa_3_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tph_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bah_ge_3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vph_remd', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('hdwplba', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('vegclass', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('eslf_code', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('iv_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('conpliv', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('iv_vs', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('svph_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('svph_50_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('lsog', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('cancov_con', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('sc_decaid', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('dvph_75_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dcov_75_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vph_50_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('sbph_ge_20_in', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('struccondr', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('bac_50_75', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dvph_ge_25', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('bah_75_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('stph_ge_100', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('trees', ['PlotSummary'])

        # Adding model 'GNN_ORWA'
        db.create_table('trees_gnn_orwa', (
            ('count', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('trees', ['GNN_ORWA'])

        # Adding model 'Parcel'
        db.create_table('trees_parcel', (
            ('geom', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(srid=3857)),
            ('apn', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('trees', ['Parcel'])

        # Adding model 'StreamBuffer'
        db.create_table('trees_streambuffer', (
            ('perimeter', self.gf('django.db.models.fields.FloatField')()),
            ('str_buf_id', self.gf('django.db.models.fields.IntegerField')()),
            ('geom', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(srid=3857)),
            ('area', self.gf('django.db.models.fields.FloatField')()),
            ('inside', self.gf('django.db.models.fields.IntegerField')()),
            ('str_buf_field', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('trees', ['StreamBuffer'])

        # Adding model 'TreeLive'
        db.create_table(u'tree_live', (
            ('plot_type', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('iv_fc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('baph_plt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('ucc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('volph_plt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('assessment_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('plot', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('volph_cc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tph_cc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('source_db', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('plot_size', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('age_bh', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('baph_fc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('mod_htm_fvs', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('volph_fc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('spp_symbol', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('rem_cc', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('iv_plt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('for_spec', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('data_source', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('fcid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('pctcov_plt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('live_id', self.gf('django.db.models.fields.BigIntegerField')(primary_key=True)),
            ('ht_est_method', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('rem_pnt', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('biomph_pnt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tph_fc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tree_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('scientific_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('baph_pnt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('biomph_cc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dbh_cm', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('tph_pnt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('ba_m2', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dbh_class', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('pnt_num', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('volph_pnt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('pctcov_cc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('pntid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('iv_cc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('biomph_fc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('hcb', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=4, blank=True)),
            ('tph_plt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('iv_pnt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('ccid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('dbh_est_method', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('ht_m', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('source_id', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('baph_cc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('cull_cubic', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('pltid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('loc_id', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('rem_plt', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('crown_class', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('rem_fc', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('pctcov_fc', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('vol_m3', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('crown_ratio', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('biomph_plt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('pctcov_pnt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('con', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
        ))
        db.send_create_signal('trees', ['TreeLive'])

        # Adding model 'PlotLookup'
        db.create_table('trees_plotlookup', (
            ('source', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('attr', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=60, null=True, blank=True)),
            ('units', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('weight', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('desc', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('trees', ['PlotLookup'])

        # Deleting field 'TreeliveSummary.class_id'
        db.delete_column(u'treelive_summary', 'class_id')

        # Deleting field 'TreeliveSummary.varname'
        db.delete_column(u'treelive_summary', 'varname')

        # User chose to not deal with backwards NULL issues for 'TreeliveSummary.cond_id'
        raise RuntimeError("Cannot reverse this migration. 'TreeliveSummary.cond_id' and its values cannot be restored.")

        # Adding unique constraint on 'TreeliveSummary', fields ['cond_id']
        db.create_unique(u'treelive_summary', ['cond_id'])


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 2, 6, 18, 57, 31, 518480)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 2, 6, 18, 57, 31, 518346)'}),
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
            'county_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'covcl': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'elev_ft': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fia_forest_type_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'firstofaspect_deg': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'for_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'for_type_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'for_type_secdry': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'for_type_secdry_name': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'forest_name': ('django.db.models.fields.CharField', [], {'max_length': '510', 'null': 'True', 'blank': 'True'}),
            'fvs_variant': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'halfstate_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'latitude_fuzz': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'longitude_fuzz': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mai': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'ogsi': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'own_group': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'plant_assoc_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
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
            'stand_age_even_yn': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'stand_size_class': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
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
        'trees.scenario': {
            'Meta': {'object_name': 'Scenario'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'trees_scenario_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_age_class': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'input_property': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['trees.ForestProperty']"}),
            'input_rxs': ('trees.models.JSONField', [], {}),
            'input_site_diversity': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'input_target_boardfeet': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'input_target_carbon': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'output_scheduler_results': ('trees.models.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'trees_scenario_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'trees_scenario_related'", 'to': "orm['auth.User']"})
        },
        'trees.stand': {
            'Meta': {'object_name': 'Stand'},
            'cond_id': ('django.db.models.fields.BigIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'trees_stand_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'geometry_final': ('django.contrib.gis.db.models.fields.PolygonField', [], {'srid': '3857', 'null': 'True', 'blank': 'True'}),
            'geometry_orig': ('django.contrib.gis.db.models.fields.PolygonField', [], {'srid': '3857', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manipulators': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'trees_stand_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'strata': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['trees.Strata']", 'null': 'True', 'blank': 'True'}),
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
