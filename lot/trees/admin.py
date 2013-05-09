from trees.models import *
from django.contrib import admin
from django import forms

admin.site.register(Strata)
admin.site.register(Stand)
admin.site.register(Scenario)
admin.site.register(ForestProperty)
admin.site.register(ScenarioStand)
admin.site.register(Rx)
admin.site.register(MyRx)
admin.site.register(SpatialConstraint)
admin.site.register(County)
admin.site.register(TreeliveSummary)
admin.site.register(IdbSummary)


class FVSVariantAdminForm(forms.ModelForm):
    class Meta:
        model = FVSVariant

    def clean_decision_tree_xml(self):
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(self.cleaned_data["decision_tree_xml"])

            # find all branches that don't have additional forks; ie terminal nodes == rx name
            rx_names = [branch.findtext('content') for branch in root.findall('branch')
                        if 'fork' not in [x.tag for x in branch.getchildren()]]

            # these should match with one rx.internal_name
            misses = []
            for rx_name in rx_names:
                try:
                    Rx.objects.get(internal_name=rx_name)
                except Rx.DoesNotExist:
                    misses.append(rx_name)
            if len(misses) > 0:
                raise ValidationError("The following Rx names don't exist in the database: " +
                                      "%s" % ',  '.join("'%s'" % m for m in misses))

        except Exception as e:
            raise ValidationError("XML error: %s" % e)
        return self.cleaned_data["decision_tree_xml"]


class FVSVariantAdmin(admin.ModelAdmin):
    form = FVSVariantAdminForm


admin.site.register(FVSVariant, FVSVariantAdmin)
