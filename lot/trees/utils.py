from trees.models import Stand, ForestProperty
from django.contrib.gis.gdal import DataSource
from django.db import transaction


class StandImporter:

    def __init__(self, forest_property):
        self.forest_property = forest_property
        self.user = self.forest_property.user
        self.required_fields = ['name']
        self.optional_fields = ['domspp','rx'] # model must provide defaults!

    def _validate_field_mapping(self, layer, field_mapping):
        fields = layer.fields

        for fname in self.required_fields:
            if fname not in field_mapping.keys():
                # if not mapped, try the attribute name directly
                field_mapping[fname] = fname

            if field_mapping[fname] not in fields:
                raise Exception("field_mapping must at least provide a 'name'")

        for fname in self.optional_fields:
            if fname not in field_mapping.keys():
                # if not mapped, try the attribute name directly
                field_mapping[fname] = fname
            
        return field_mapping

    def import_ogr(self, shp_path, field_mapping = {}, layer_num = 0):
        ds = DataSource(shp_path)
        layer = ds[0]
        num_features = len(layer)
        field_mapping = self._validate_field_mapping(layer, field_mapping)

        for feature in layer:
            stand1 = Stand(user=self.user, 
                    name=feature.get(field_mapping['name']), 
                    geometry_orig=feature.geom.geos) 

            for fname in self.optional_fields:
                if fname in field_mapping.keys():
                    stand1.__dict__[fname] = feature.get(field_mapping[fname])

            stand1.save()
            self.forest_property.add(stand1)
            del stand1

        transaction.rollback()


