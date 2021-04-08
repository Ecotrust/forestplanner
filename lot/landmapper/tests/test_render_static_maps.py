import os, sys

from django.test import TestCase, Client
from django.conf import settings
# from selenium import webdriver

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from landmapper.models import Property, Taxlot
from landmapper.map_layers import views as map_views


class RenderTest(TestCase):
    def setUp(self):


        # try:
        #     webdriver.DesiredCapabilities.FIREFOX["unexpectedAlertBehaviour"] = "accept"
        #     self.browser = webdriver.Firefox()
        # except Exception as e:
        #     print(e)
        #     print("Have you installed xvfb?")
        #     print("Have you run `Xvfb :99 -ac &` since you last restarted?")
        #     print("Have you run `export DISPLAY=:99` since you last restarted?")
        #     sys.exit(1)
        pass

    def test_render_basemap(self):
        import geopandas as gpd
        from landmapper.reports import get_property_specs, refit_bbox, get_collection_from_object, get_gdf_from_features, merge_rasters_to_img
        user = User()
        taxlot_multipolygon = GEOSGeometry('''
            {
                "type": "MultiPolygon",
                "coordinates": [ [ [ [ -13707214.868887795135379, 5346534.2430977569893 ], [ -13707260.774380918592215, 5346533.97550374828279 ], [ -13707261.944770587608218, 5346612.806692086160183 ], [ -13707263.715054979547858, 5346732.017174454405904 ], [ -13707286.692351568490267, 5346731.639577495865524 ], [ -13707286.933646179735661, 5346773.196871299296618 ], [ -13707153.935666222125292, 5346773.180854049511254 ], [ -13707142.001171046867967, 5346749.72015602234751 ], [ -13707121.206178674474359, 5346714.79005856346339 ], [ -13707084.687287205830216, 5346691.29145734384656 ], [ -13707094.261487463489175, 5346678.048360565677285 ], [ -13707142.23308670707047, 5346627.786874319426715 ], [ -13707150.594486435875297, 5346620.10307655762881 ], [ -13707165.760785942897201, 5346606.165980608202517 ], [ -13707185.012686328962445, 5346580.619886935688555 ], [ -13707185.361286334693432, 5346580.170087040401995 ], [ -13707185.709286341443658, 5346579.719587155617774 ], [ -13707186.056286348029971, 5346579.268387268297374 ], [ -13707186.402486354112625, 5346578.816587388515472 ], [ -13707186.747986359521747, 5346578.364087495021522 ], [ -13707187.09248636290431, 5346577.911087609827518 ], [ -13707187.436286373063922, 5346577.45738772302866 ], [ -13707187.779286380857229, 5346577.003087832592428 ], [ -13707188.12138638459146, 5346576.548087951727211 ], [ -13707188.462686391547322, 5346576.092588063329458 ], [ -13707188.803086400032043, 5346575.636388170532882 ], [ -13707189.142786405980587, 5346575.179588284343481 ], [ -13707189.48158641345799, 5346574.722188394516706 ], [ -13707189.819586418569088, 5346574.264088512398303 ], [ -13707190.156686430796981, 5346573.80538862477988 ], [ -13707190.492986442521214, 5346573.346188731491566 ], [ -13707190.828386450186372, 5346572.886288844980299 ], [ -13707191.163086457177997, 5346572.425788959488273 ], [ -13707191.496986461803317, 5346571.96458906494081 ], [ -13707191.829886479303241, 5346571.50288918055594 ], [ -13707192.161986485123634, 5346571.040589299984276 ], [ -13707192.493186494335532, 5346570.577689404599369 ], [ -13707192.823786504566669, 5346570.11408952344209 ], [ -13707193.153286509215832, 5346569.649889628402889 ], [ -13707193.481986520811915, 5346569.185189744457603 ], [ -13707193.809986533597112, 5346568.719789859838784 ], [ -13707194.137086544185877, 5346568.253889968618751 ], [ -13707194.463286556303501, 5346567.787290081381798 ], [ -13707194.788586566224694, 5346567.32009020075202 ], [ -13707195.113086577504873, 5346566.852490305900574 ], [ -13707195.436786593869328, 5346566.384090418927372 ], [ -13707195.759586604312062, 5346565.915090530179441 ], [ -13707196.081586616113782, 5346565.445690639317036 ], [ -13707196.402686627581716, 5346564.975490757264197 ], [ -13707196.723086640238762, 5346564.504890867508948 ], [ -13707197.04248665086925, 5346564.033590978942811 ], [ -13707197.360986661165953, 5346563.561591091565788 ], [ -13707197.678586672991514, 5346563.089291201904416 ], [ -13707197.995586691424251, 5346562.616291316226125 ], [ -13707198.311486706137657, 5346562.142591428011656 ], [ -13707198.626586718484759, 5346561.668491534888744 ], [ -13707198.940886732190847, 5346561.193691652268171 ], [ -13707199.254186743870378, 5346560.718391766771674 ], [ -13707199.566786760464311, 5346560.242491878569126 ], [ -13707199.878386773169041, 5346559.766091983765364 ], [ -13707200.189186787232757, 5346559.288992095738649 ], [ -13707200.499186798930168, 5346558.811392207629979 ], [ -13707200.808186819776893, 5346558.333192326128483 ], [ -13707201.116486830636859, 5346557.854492436163127 ], [ -13707201.423786850646138, 5346557.375192541629076 ], [ -13707201.730186862871051, 5346556.89529265742749 ], [ -13707202.035786878317595, 5346556.414992765523493 ], [ -13707202.340586896985769, 5346555.933992881327868 ], [ -13707202.644386911764741, 5346555.452392990700901 ], [ -13707202.947386929765344, 5346554.970293097198009 ], [ -13707203.249386945739388, 5346554.487693215720356 ], [ -13707203.550586961209774, 5346554.004493326880038 ], [ -13707203.851086977869272, 5346553.520693439058959 ], [ -13707204.15048699453473, 5346553.036493547260761 ], [ -13707204.448987012729049, 5346552.551593663170934 ], [ -13707204.746687034144998, 5346552.066293767653406 ], [ -13707205.04348704405129, 5346551.580293883569539 ], [ -13707205.339487066492438, 5346551.093793992884457 ], [ -13707205.634587086737156, 5346550.606794103980064 ], [ -13707205.92868710309267, 5346550.119294219650328 ], [ -13707206.221987122669816, 5346549.631194330751896 ], [ -13707206.514287142083049, 5346549.14249443821609 ], [ -13707206.805787162855268, 5346548.653394544497132 ], [ -13707207.096387177705765, 5346548.163694660179317 ], [ -13707207.386187203228474, 5346547.673594772815704 ], [ -13707207.674987221136689, 5346547.182794884778559 ], [ -13707207.9629872366786, 5346546.691494995728135 ], [ -13707208.249987259507179, 5346546.199595103040338 ], [ -13707208.536087280139327, 5346545.707395217381418 ], [ -13707208.821487298235297, 5346545.214495332911611 ], [ -13707209.105787320062518, 5346544.721095438115299 ], [ -13707209.389187337830663, 5346544.227195548824966 ], [ -13707209.671787358820438, 5346543.732795657590032 ], [ -13707209.953487377613783, 5346543.237995765171945 ], [ -13707210.234287399798632, 5346542.742495882324874 ], [ -13707210.514087427407503, 5346542.246495989151299 ], [ -13707210.792987447232008, 5346541.750096103176475 ], [ -13707211.071187470108271, 5346541.253096214495599 ], [ -13707211.348287492990494, 5346540.755696321837604 ], [ -13707211.624587515369058, 5346540.257696425542235 ], [ -13707211.89998753555119, 5346539.759296545758843 ], [ -13707212.174387557432055, 5346539.260296654887497 ], [ -13707212.447987576946616, 5346538.760796764865518 ], [ -13707212.72058760561049, 5346538.260696872137487 ], [ -13707212.992287628352642, 5346537.76019698753953 ], [ -13707213.263187654316425, 5346537.25929709803313 ], [ -13707213.532987678423524, 5346536.757797203026712 ], [ -13707213.801987703889608, 5346536.255897318013012 ], [ -13707214.070187725126743, 5346535.753397422842681 ], [ -13707214.337387749925256, 5346535.250397533178329 ], [ -13707214.603587774559855, 5346534.746997647918761 ], [ -13707214.868887795135379, 5346534.2430977569893 ] ] ] ]
            }
        ''')
        taxlot_multipolygon.srid = 3857
        property = Property(user=user,
                            geometry_orig=taxlot_multipolygon,
                            name='Buckhorn')
        # given a property, get the coordinates
        coords = property.geometry_orig.coords
        self.assertTrue(len(coords) > 0)

        # convert those coordinates into a buffered bounding box
        # (bbox, orientation) = map_views.get_bbox_from_property(property)
        property_specs = get_property_specs(property)
        self.assertTrue(len(property_specs['bbox']) > 0)

        property_bboxes = {
            'fit': property_specs['bbox'],
            'medium': refit_bbox(property_specs, scale='medium'),
            'context': refit_bbox(property_specs, scale='context')
        }

        def_bbox_lims = property_bboxes['fit'].split(',')
        def_w, def_s, def_e, def_n = [float(x) for x in def_bbox_lims]
        self.assertTrue(def_w)
        self.assertTrue(def_n)

        # get appropriate bounding box for street maps
        st_bbox_lims = property_bboxes['context'].split(',')
        st_w, st_s, st_e, st_n = [float(x) for x in st_bbox_lims]
        self.assertTrue(st_w)
        self.assertTrue(st_w < def_w)
        self.assertTrue(st_n)
        self.assertTrue(st_n > def_n)

        # get appropriate bounding box for topo map
        top_w, top_s, top_e, top_n = [float(x) for x in property_bboxes['medium'].split(',')]
        self.assertTrue(top_w)
        self.assertTrue(top_w < def_w)
        self.assertTrue(top_w > st_w)
        self.assertTrue(top_n)
        self.assertTrue(top_n > def_n)
        self.assertTrue(top_n < st_n)


        # get property as a geodataframe
        property_collection = get_collection_from_object(property, 'geometry_orig', property_bboxes['fit'])
        property_gdf = get_gdf_from_features(property_collection)
        self.assertEqual(type(property_gdf), gpd.geodataframe.GeoDataFrame)
        self.assertEqual(property_gdf.area.values[0], 28940.37884117589)

        # get aerial image
        img_height = settings.REPORT_MAP_HEIGHT
        img_width = settings.REPORT_MAP_WIDTH

        out_dir = os.path.join(settings.LANDMAPPER_DIR, 'tests', 'output')
        outfile = os.path.join(out_dir, 'aerial.png')
        aerial_layer = map_views.get_aerial_image_layer(property_specs, property_bboxes[settings.AERIAL_SCALE])
        aerial_layer['image'].save(outfile, "PNG")
        self.assertEqual(aerial_layer['image'].width, img_width)
        self.assertEqual(aerial_layer['image'].height, img_height)

        # get attribution image
        attributions = [
            aerial_layer['attribution'],
            settings.TAXLOTS_URLS['MAPBOX_TILE']['ATTRIBUTION']
        ]
        width = property_specs['width']
        height = property_specs['height']
        attribution_image = map_views.get_attribution_image(attributions, width, height)
        self.assertEqual(attribution_image.width, img_width)
        self.assertEqual(attribution_image.height, img_height)

        # render the aerial imagery, property, and attrs to a properly-sized .png (Overview)

        # layers as a reverse stack (pulled into new stack from top to bottom, so layers[0] -> bottom and layers[-1] -> top)
        layers = [
            {"type": 'img', "layer":aerial_layer['image']},
            {"type": 'gdf', "layer":property_gdf, "style": settings.PROPERTY_STYLE},
            {"type": 'img', "layer":attribution_image},
        ]

        overview_image = merge_rasters_to_img(layers, bbox=property_specs['bbox'], img_height=img_height, img_width=img_width)

        outfile = os.path.join(out_dir, 'overview.png')
        overview_image.save(outfile, "PNG")

        #   -- Get count of purple (boundary) pixels!
        fit_purps = 0
        for pixel in overview_image.getdata():
            if pixel == (255, 0, 255, 255):
                fit_purps += 1
        self.assertTrue(fit_purps > 1000) # likely ~5330 pixels

        # property.property_map_image = map_views.get_property_map(
        #     property_specs,
        #     base_layer=aerial_layer,
        #     property_layer=property_layers[settings.PROPERTY_OVERVIEW_SCALE]
        # )

        # get taxlots as a geodataframe

        # get updated attribution image

        # render attrs atop property atop taxlots atop aerial (Aerial)

        # render property atop streets
        #   -- Compare purple pixel count

        # render property atop terrain
        #   -- Compare purple pixel count

        # render property atop streams atop aerial

        # render property atop soils atop aerial

        # render property atop forest types atop ???
