from trees.models import Stand, ForestProperty
from django.contrib.gis.gdal import DataSource

class StandImporter:

    def __init__(self, forest_property):
        self.forest_property = forest_property
        self.user = self.forest_property.user

    def _validate_field_mapping(self, field_mapping):
        if 'name' not in field_mapping.keys():
            raise Exception("field_mapping must at least provide a 'name'")
        return True

    def import_ogr(self, shp_path, field_mapping, layer_num = 0):
        ds = DataSource(shp_path)
        layer = ds[0]
        self._validate_field_mapping(field_mapping)

        for feature in layer:
            stand1 = Stand(user=self.user, 
                    name=feature.get(field_mapping['name']), 
                    geometry_orig=feature.geom.geos) 
            stand1.save()
            self.forest_property.add(stand1)
            del stand1


