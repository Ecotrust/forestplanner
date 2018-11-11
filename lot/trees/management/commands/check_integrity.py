from django.core.management.base import BaseCommand
from trees.models import FVSVariant, Rx, RX_TYPE_CHOICES
import xml.etree.ElementTree as ET
from django.db import connection
from sets import Set


class Command(BaseCommand):

    def violation(self, msg):
        self.errors += 1
        print msg

    def handle(self, *args, **options):

        self.errors = 0
        cursor = connection.cursor()

        #
        # FVSAggregate
        # Check that all Variants, Rxs and Conditions referenced in FVSAggregate table
        #
        def compare_distinct(ref_table, ref_col, comp_table, comp_col, cast=int):

            ref_sql = "SELECT distinct(%s) FROM %s" % (ref_col, ref_table)
            cursor.execute(ref_sql)
            ref = Set([cast(x[0]) for x in list(cursor.fetchall())])

            comp_sql = "SELECT distinct(%s) FROM %s" % (comp_col, comp_table)
            cursor.execute(comp_sql)
            comp = Set([cast(x[0]) for x in list(cursor.fetchall())])

            diff = ref.difference(comp)
            ndiff = len(diff)
            if ndiff > 0:
                self.errors += ndiff - 1
                self.violation("* %s has %d %s that are NOT in %s. \n  %r" % (
                    ref_table, ndiff, ref_col, comp_table, list(diff)[:4] + ["..."]))

            diff = comp.difference(ref)
            ndiff = len(diff)
            if ndiff > 0:
                self.errors += ndiff - 1
                self.violation("* %s is missing %d %s that are found in %s. \n  %r" % (
                    ref_table, ndiff, ref_col, comp_table, list(diff)[:4] + ["..."]))

        compare_distinct("trees_fvsaggregate", "cond", "treelive_summary", "cond_id")
        compare_distinct("trees_fvsaggregate", "cond", "trees_conditionvariantlookup", "cond_id")
        compare_distinct("trees_fvsaggregate", "cond", "idb_summary", "cond_id")

        compare_distinct("trees_conditionvariantlookup", "cond_id", "treelive_summary", "cond_id")
        compare_distinct("trees_conditionvariantlookup", "cond_id", "idb_summary", "cond_id")
        compare_distinct("trees_conditionvariantlookup", "variant_code", "trees_fvsvariant", "code", cast=str)

        #
        # Decision Tree XMLS
        #
        rxs_covered = []
        for variant in FVSVariant.objects.all():

            if not variant.decision_tree_xml:
                self.violation("Variant %s decision_tree_xml is empty." % (variant))
                continue

            try:
                root = ET.fromstring(variant.decision_tree_xml)
            except:
                self.violation("Variant %s decision_tree_xml is not valid xml." % (variant))
                continue

            # find all branches that don't have additional forks; ie terminal nodes == rx name
            rx_names = [branch.findtext('content') for branch in root.findall('branch')
                        if 'fork' not in [x.tag for x in branch.getchildren()]]

            # these should match with one rx.internal_name
            for rx_name in rx_names:
                try:
                    Rx.objects.get(internal_name=rx_name)
                    rxs_covered.append(rx_name)
                    #print rx_name, "covered"
                except Rx.DoesNotExist:
                    self.violation("Variant %s decision_tree_xml references Rx with internal_name %s that does't exist" % (variant, rx_name))

        missing_rxs = Rx.objects.exclude(internal_name__in=rxs_covered)
        for missing_rx in missing_rxs:
            self.violation("Rx %s is not referenced in any variant's decision_tree_xml" % (missing_rx.internal_name))

        #
        # Default Rx types
        #
        for variant in FVSVariant.objects.all():
            # All non-NA RX types should be represented by one and only one Rx per variant
            for rx_choice in RX_TYPE_CHOICES:
                if rx_choice[0] == "NA":
                    # don't worry about NA rxs
                    continue
                try:
                    Rx.objects.get(variant=variant, internal_type=rx_choice[0])
                except Rx.DoesNotExist:
                    self.violation("Rx with type %s (%s) doesn't exist in %s but should according to RX_TYPE_CHOICES" % (
                        rx_choice[0], rx_choice[1], variant))
        #
        # User Features
        # TODO - do we check this here? This could be a separate issue...
        # check all user features (stands, scenariostands) that relate to variant, rx and cond_id and make sure they are referenced
        # in FVSVariant, Rx and IdbSummary/TreeliveSummary/FVSAggregate
        #

        print
        print "check_integrity summary: %d violations that should be addressed" % self.errors
        print
        print " For further discussion on integrity_errors, see:"
        print " https://github.com/Ecotrust/forestplanner/wiki/IDB-data-processing#potential-check_integrity-errors"
        print