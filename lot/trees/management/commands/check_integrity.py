import os
from django.core.management.base import BaseCommand
from trees.models import ForestProperty, Stand, FVSVariant, IdbSummary, ScenarioStand, ConditionVariantLookup, Rx, RX_TYPE_CHOICES
import xml.etree.ElementTree as ET


class Command(BaseCommand):

    def violation(self, msg):
        self.errors += 1
        print msg

    def handle(self, *args, **options):

        self.errors = 0

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
        # ConditionVariantLookups
        #
        cond_ids = [x.cond_id for x in IdbSummary.objects.all()]
        variant_codes = [x.code for x in FVSVariant.objects.all()]

        # check that all lookups have valid references
        for cvl in ConditionVariantLookup.objects.all():
            if cvl.cond_id not in cond_ids:
                self.violation(
                    "ConditionVariantLookup table referen in the lookup tableces cond_id " +
                    "%s which doesn't exist in IdbSummary" % cvl.cond_id)
            if cvl.variant_code not in variant_codes:
                self.violation(
                    "ConditionVariantLookup table references variant code " +
                    "%s which doesn't exist in FVSVariant" % cvl.variant_code)

        # check that all IdbSummaries are present in the lookup table
        lookup_cond_ids = [x.cond_id for x in ConditionVariantLookup.objects.all()]
        for cond_id in cond_ids:
            if cond_id not in lookup_cond_ids:
                self.violation("Missing cond_id %s from ConditionVariantLookup table" % cond_id)

        #
        # FVSAggregate
        # TODO
        # Check that all Variants, Rxs and Conditions referenced in FVSAggregate table
        # exist in the FVSVariant, Rx and IdbSummary/TreeliveSummary tables
        #

        #
        # User Features
        # TODO - do we check this here? This could be a separate issue...
        # check all user features that relate to variant, rx and cond_id and make sure they are referenced
        # in FVSVariant, Rx and IdbSummary/TreeliveSummary/FVSAggregate
        #

        print
        print "check_integrity summary: %d violations that should be addressed" % self.errors
        print
