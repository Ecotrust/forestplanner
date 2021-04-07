import os, io, datetime, requests, json, decimal
from datetime import date
from django.conf import settings
from django.contrib.humanize.templatetags import humanize
import geopandas as gpd
from landmapper.models import SoilType
from landmapper.fetch import soils_from_nrcs
from landmapper.map_layers import views as map_views
from matplotlib import pyplot as plt
import numpy as np
from pdfjinja import PdfJinja
from PIL import Image
import PyPDF2 as pypdf
from rasterio import transform
from rasterio.plot import show, reshape_as_raster
from tempfile import NamedTemporaryFile

def refit_bbox(property_specs, scale='fit'):
    # bbox: string of EPSG:3857 coords formatted as "W,S,E,N"
    bbox = property_specs['bbox']
    pixel_width = property_specs['width']
    pixel_height = property_specs['height']

    min_resolution = False
    if scale == 'medium':
        min_resolution = settings.MAX_WEB_MERCATOR_RESOLUTION_MEDIUM
    if scale == 'context':
        min_resolution = settings.MAX_WEB_MERCATOR_RESOLUTION_CONTEXT

    if min_resolution:
        # Get bbox width in Web Mercator Degrees (EPSG:3857)
        [west, south, east, north] = bbox.split(',')
        mercator_width = abs(float(east)-float(west)) # this should always be pos, but abs for good measure
        mercator_height = abs(float(north)-float(south)) # this should always be pos, but abs for good measure
        # divide bbox (m) by width (px)
        fit_resolution = mercator_width/pixel_width
        # compare to 'min_resolution'
        if fit_resolution < min_resolution:
            # decrease res to meet settings
            min_web_mercator_width = min_resolution*pixel_width
            # is w:h ratio maintained in web mercator? Tested in QGIS: yes.
            min_web_mercator_height = min_resolution*pixel_height
            width_buffer = (min_web_mercator_width-mercator_width)/2
            height_buffer = (min_web_mercator_height-mercator_height)/2
            # Recalculate bbox in original projection/ratio
            new_N = float(north) + height_buffer
            new_S = float(south) - height_buffer
            new_W = float(west) - width_buffer
            new_E = float(east) + width_buffer
            bbox = "%f,%f,%f,%f" % (new_W, new_S, new_E, new_N)

    return bbox

def get_property_report(property, taxlots):
    # TODO: call this in "property" after creating the object instance

    # calculate orientation, w x h, bounding box, centroid, and zoom level
    property_specs = get_property_specs(property)

    property_bboxes = {
        'fit': property_specs['bbox'],
        'medium': refit_bbox(property_specs, scale='medium'),
        'context': refit_bbox(property_specs, scale='context')
    }
    # TODO: Replace with getting a property geodataframe
    property_layers = {
        'fit': map_views.get_property_image_layer(property, property_specs),
        'medium': map_views.get_property_image_layer(
            property, property_specs, property_bboxes['medium']
        ),
        'context': map_views.get_property_image_layer(
            property, property_specs, property_bboxes['context']
        )
    }

    # TODO: Replace this with taxlot dataframe
    taxlot_layer = map_views.get_taxlot_image_layer(property_specs, property_bboxes[settings.TAXLOTS_SCALE])
    aerial_layer = map_views.get_aerial_image_layer(property_specs, property_bboxes[settings.AERIAL_SCALE])
    street_layer = map_views.get_street_image_layer(property_specs, property_bboxes[settings.STREET_SCALE])
    topo_layer = map_views.get_topo_image_layer(property_specs, property_bboxes[settings.TOPO_SCALE])
    if settings.CONTOUR_SOURCE:
        contour_layer = map_views.get_contour_image_layer(property_specs, property_bboxes[settings.CONTOUR_SCALE])
    else:
        contour_layer = False
    # TODO: Replace this with soil dataframe
    soil_layer = map_views.get_soil_image_layer(property_specs, property_bboxes[settings.SOIL_SCALE])
    # TODO: Replace this with stream dataframe (?)
    stream_layer = map_views.get_stream_image_layer(property_specs, property_bboxes[settings.STREAM_SCALE])

    # TODO: Rewrite to use MatPlotLib,dataframes, and Images
    property.property_map_image = map_views.get_property_map(
        property_specs,
        base_layer=aerial_layer,
        property_layer=property_layers[settings.PROPERTY_OVERVIEW_SCALE]
    )
    # TODO: Rewrite to use MatPlotLib,dataframes, and Images
    property.aerial_map_image = map_views.get_aerial_map(
        property_specs,
        base_layer=aerial_layer,
        lots_layer=taxlot_layer,
        property_layer=property_layers[settings.AERIAL_SCALE]
    )
    # TODO: Rewrite to use MatPlotLib,dataframes, and Images
    property.street_map_image = map_views.get_street_map(
        property_specs,
        base_layer=street_layer,
        property_layer=property_layers[settings.STREET_SCALE]
    )
    # TODO: Rewrite to use MatPlotLib,dataframes, and Images
    property.terrain_map_image = map_views.get_terrain_map(
        property_specs,
        base_layer=topo_layer,
        property_layer=property_layers[settings.TOPO_SCALE],
        contour_layer=contour_layer
    )
    if settings.STREAMS_BASE_LAYER == 'aerial':
        stream_base_layer = aerial_layer
    else:
        stream_base_layer = topo_layer
    # TODO: Rewrite to use MatPlotLib,dataframes, and Images
    property.stream_map_image = map_views.get_stream_map(
        property_specs,
        base_layer=stream_base_layer,
        stream_layer=stream_layer,
        property_layer=property_layers[settings.STREAM_SCALE])
    # TODO: Rewrite to use MatPlotLib,dataframes, and Images
    property.soil_map_image = map_views.get_soil_map(
        property_specs,
        base_layer=aerial_layer,
        lots_layer=taxlot_layer,
        soil_layer=soil_layer,
        property_layer=property_layers[settings.SOIL_SCALE])

    property.scalebar_image = map_views.get_scalebar_image(property_specs,
                                                           span_ratio=0.75
    )
    property.context_scalebar_image = map_views.get_scalebar_image(
        {'width': property_specs['width'], 'bbox': property_bboxes['context']},
        span_ratio=0.75
    )
    property.medium_scalebar_image = map_views.get_scalebar_image(
        {'width': property_specs['width'], 'bbox': property_bboxes['medium']},
        span_ratio=0.75
    )

    property.report_data = get_property_report_data(property, property_specs,
                                                    taxlots)

def get_property_report_data(property, property_specs, taxlots):
    report_data = {
        # '${report_page_name}': {
        #     'data': [ 2d array, 1 row for each entry, 1 column for each attr, 1st col is name],
        # }
    }
    report_pages = [
        'property', 'aerial', 'street', 'terrain', 'streams', 'soils',
        'forest_type'
    ]

    report_data['date'] = date.today().strftime("%B %d, %Y")

    #Property
    property_data = get_aggregate_property_data(property, taxlots)

    report_data['property'] = {'data': property_data, 'legend': None}

    #aerial
    aerial_data = None

    report_data['aerial'] = {
        'data': aerial_data,
        'legend': settings.AERIAL_MAP_LEGEND_URL
    }

    #street
    street_data = None

    report_data['street'] = {
        'data': street_data,
        'legend': settings.STREET_MAP_LEGEND_URL
    }

    #terrain
    terrain_data = None

    report_data['terrain'] = {
        'data': terrain_data,
        'legend': settings.TERRAIN_MAP_LEGEND_URL
    }

    #streams
    streams_data = None

    report_data['streams'] = {
        'data': streams_data,
        'legend': settings.STREAM_MAP_LEGEND_URL
    }

    #soils
    soil_data = get_soils_data(property.geometry_orig)

    report_data['soils'] = {
        'data': soil_data,
        'legend': settings.SOIL_MAP_LEGEND_URL
    }

    #forest_type
    forest_type_data = None

    report_data['forest_type'] = {
        'data': forest_type_data,
        'legend': settings.FOREST_TYPE_MAP_LEGEND_URL
    }

    return report_data

## handles summarization of property attributes
def get_aggregate_property_data(property, taxlots):
    acres = []
    sq_miles = []
    min_elevation = []
    max_elevation = []
    legal = []
    odf_fpd = []
    agency = []
    orzdesc = []
    huc12 = []
    name = []
    twnshpno = []
    rangeno = []
    frstdivno = []
    # mean_elevation = []

    for taxlot in taxlots:
        acres.append(taxlot.area_in_acres)
        min_elevation.append(taxlot.min_elevation)
        max_elevation.append(taxlot.max_elevation)
        legal.append("%s" %
                     (taxlot.legal_label))
        agency.append(taxlot.agency)
        odf_fpd.append(taxlot.odf_fpd)
        name.append(taxlot.name)
        huc12.append(taxlot.huc12)
        orzdesc.append(taxlot.orzdesc)

    min_elevation = pretty_print_float(m_to_ft(aggregate_min(min_elevation)))
    max_elevation = pretty_print_float(m_to_ft(aggregate_max(max_elevation)))

    if not min_elevation == None and not max_elevation == None:
        elevation_label = 'Elevation Range'
        elevation_value = "%s - %s ft" % (min_elevation, max_elevation)
    else:
        elevation_label = 'Elevation'
        elevation_value = 'Unknown'

    return [
        ['Acres',
         pretty_print_float(aggregate_sum(acres))],
        [elevation_label, elevation_value],
        ['Legal Description', aggregate_strings(legal)],
        ['Structural Fire Disctrict',
         aggregate_strings(agency)],
        ['Forest Fire District',
         aggregate_strings(odf_fpd)], ['Watershed',
                                       aggregate_strings(name)],
        ['Watershed (HUC)', aggregate_strings(huc12)],
        ['Zoning', aggregate_strings(orzdesc)]
        # ['twnshpno', aggregate_strings(twnshpno)],
        # ['rangeno', aggregate_strings(rangeno)],
        # ['frstdivno', aggregate_strings(frstdivno)],
    ]

def aggregate_strings(agg_list):
    agg_list = [x for x in agg_list if not x == None]
    out_str = '; '.join(list(dict.fromkeys(agg_list)))
    if len(out_str) == 0:
        out_str = "None"
    return out_str

def aggregate_min(agg_list):
    out_min = None
    for min in agg_list:
        if out_min == None:
            out_min = min
        if min:
            if min < out_min:
                out_min = min
    return out_min

def aggregate_max(agg_list):
    out_max = None
    for max in agg_list:
        if out_max == None:
            out_max = max
        if max:
            if max > out_max:
                out_max = max
    return out_max

def aggregate_mean(agg_list):
    mean_sum = 0
    for mean in agg_list:
        if not mean == None:
            mean_sum += mean
    return mean_sum / len(agg_list)

def aggregate_sum(agg_list):
    sum_total = 0
    for sum in agg_list:
        if not sum == None:
            sum_total += sum
    return sum_total

# Area Unit Conversion
def sq_ft_to_acres(sq_ft_val):
    return sq_ft_val / 43560

def sq_m_to_acres(sq_m_val):
    return sq_m_val / 4046.86

# Length Unit Conversion
def cm_to_inches(cm_val):
    if cm_val:
        return float(cm_val) / 2.54
    else:
        return cm_val

def m_to_ft(m_val):
    if m_val:
        return float(m_val) * 3.28084
    else:
        return m_val

def pretty_print_float(value):
    if isinstance(value, (int, float, decimal.Decimal)):
        if abs(value) >= 1000000:
            return humanize.intword(round(value))
        elif abs(value) >= 1000:
            return humanize.intcomma(round(value))
        elif abs(value) >= 100:
            return str(round(value))
        elif abs(value) >= 1:
            return format(value, '.3g')
        else:
            return format(value, '.3g')
    elif value:
        return str(value)
    else:
        return value # None

def get_property_specs(property):
    property_specs = {
        'orientation': None,  # 'portrait' or 'landscape'
        'width': None,  # Pixels
        'height': None,  # Pixels
        'bbox': None,  # "W,S,E,N" (EPSG:3857, Web Mercator)
        'zoom': None  # {'lat': (EPSG:4326 float), 'lon': (EPSG:4326 float), 'zoom': float}
    }
    (bbox, orientation) = map_views.get_bbox_from_property(property)

    property_specs['orientation'] = orientation
    property_specs['bbox'] = bbox

    width = settings.REPORT_MAP_WIDTH
    height = settings.REPORT_MAP_HEIGHT

    if orientation.lower() == 'portrait' and settings.REPORT_SUPPORT_ORIENTATION:
        temp_width = width
        width = height
        height = temp_width

    property_specs['width'] = width
    property_specs['height'] = height

    property_specs['zoom'] = map_views.get_web_map_zoom(bbox,
                                                        width=width,
                                                        height=height,
                                                        srs='EPSG:3857')

    return property_specs

## might belong in create_property_pdf
def get_report_data_dict(data):
    data_dict = {}
    for property, value in data:
        if property == 'Acres':
            data_dict['acres'] = value
        elif property in ['Elevation', 'Elevation Range']:
            data_dict['elevation'] = value
        elif property == 'Legal Description':
            data_dict['legalDesc'] = value
        elif property == 'Structural Fire Disctrict':
            data_dict['structFire'] = value
        elif property == 'Forest Fire District':
            data_dict['fire'] = value
        elif property == 'Watershed':
            data_dict['watershed'] = value
        elif property == 'Watershed (HUC)':
            data_dict['watershedNum'] = value
        elif property == 'Zoning':
            data_dict['zone'] = value
        else:
            data_dict[property.lower()] = value

    return data_dict

def create_property_pdf(property, property_id):
    '''
    HOW TO CREATE PDFs
    ----------
    template_pdf_file : str
        path to path to the template PDF
    rendered_pdf : function (dict)
        dict - fields to populate and the values to populate them with
        function - uses pdfjinja to crete pdf
    output_file_location : str, path to file
        path to the PDF output file that will be generated
    '''
    property_url = settings.APP_URL + '/report/' + property_id + '/property/map'
    aerial_url = settings.APP_URL + '/report/' + property_id + '/aerial/map'
    street_url = settings.APP_URL + '/report/' + property_id + '/street/map'
    terrain_url = settings.APP_URL + '/report/' + property_id + '/terrain/map'
    stream_url = settings.APP_URL + '/report/' + property_id + '/stream/map'
    soil_types_url = settings.APP_URL + '/report/' + property_id + '/soil_types/map'
    scalebar_url = settings.APP_URL + '/report/' + property_id + '/scalebar/pdf'

    property_image = requests.get(property_url, stream=True)
    aerial_image = requests.get(aerial_url, stream=True)
    street_image = requests.get(street_url, stream=True)
    terrain_image = requests.get(terrain_url, stream=True)
    stream_image = requests.get(stream_url, stream=True)
    soil_image = requests.get(soil_types_url, stream=True)
    property_scalebar_image = requests.get(scalebar_url+'/fit', stream=True)
    property_context_scalebar_image = requests.get(scalebar_url+'/context', stream=True)
    property_medium_scalebar_image = requests.get(scalebar_url+'/medium', stream=True)

    tmp_property = NamedTemporaryFile(suffix='.png',
                                      dir=settings.PROPERTY_REPORT_PDF_DIR,
                                      delete=True)
    tmp_property_name = tmp_property.name
    with open(tmp_property_name, 'wb') as f:
        for chunk in property_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_aerial = NamedTemporaryFile(suffix='.png',
                                    dir=settings.PROPERTY_REPORT_PDF_DIR,
                                    delete=True)
    tmp_aerial_name = tmp_aerial.name
    with open(tmp_aerial_name, 'wb') as f:
        for chunk in aerial_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_street = NamedTemporaryFile(suffix='.png',
                                    dir=settings.PROPERTY_REPORT_PDF_DIR,
                                    delete=True)
    tmp_street_name = tmp_street.name
    with open(tmp_street_name, 'wb') as f:
        for chunk in street_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_topo = NamedTemporaryFile(suffix='.png',
                                  dir=settings.PROPERTY_REPORT_PDF_DIR,
                                  delete=True)
    tmp_topo_name = tmp_topo.name
    with open(tmp_topo_name, 'wb') as f:
        for chunk in terrain_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_stream = NamedTemporaryFile(suffix='.png',
                                    dir=settings.PROPERTY_REPORT_PDF_DIR,
                                    delete=True)
    tmp_stream_name = tmp_stream.name
    with open(tmp_stream_name, 'wb') as f:
        for chunk in stream_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    tmp_soils = NamedTemporaryFile(suffix='.png',
                                   dir=settings.PROPERTY_REPORT_PDF_DIR,
                                   delete=True)
    tmp_soils_name = tmp_soils.name
    with open(tmp_soils_name, 'wb') as f:
        for chunk in soil_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


    tmp_scalebar = NamedTemporaryFile(suffix='.png',
                                      dir=settings.PROPERTY_REPORT_PDF_DIR,
                                      delete=True)
    tmp_scalebar_name = tmp_scalebar.name
    with open(tmp_scalebar_name, 'wb') as f:
        for chunk in property_scalebar_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    # tmp_context_scalebar_name
    tmp_context_scalebar = NamedTemporaryFile(suffix='.png',
                                      dir=settings.PROPERTY_REPORT_PDF_DIR,
                                      delete=True)
    tmp_context_scalebar_name = tmp_context_scalebar.name
    with open(tmp_context_scalebar_name, 'wb') as f:
        for chunk in property_context_scalebar_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    # tmp_medium_scalebar_name
    tmp_medium_scalebar = NamedTemporaryFile(suffix='.png',
                                      dir=settings.PROPERTY_REPORT_PDF_DIR,
                                      delete=True)
    tmp_medium_scalebar_name = tmp_medium_scalebar.name
    with open(tmp_medium_scalebar_name, 'wb') as f:
        for chunk in property_medium_scalebar_image.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    # 1. write API to create local URL /landmapper/overview_map/{{ taxlot_ids }}/
    # 2. wirte .... /rest of maps

    # 1. give each image a unique name
    # 2. write images to media as files
    # 3. create PDF
    # 4. assign pdf to variable
    # 5. delete image files
    # 6. return pdf variable

    template_pdf_file = settings.PROPERTY_REPORT_PDF_TEMPLATE
    template_pdf = PdfJinja(template_pdf_file)

    current_datetime = datetime.datetime.now()
    current_datetime = current_datetime.strftime("%c")

    report_data_dict = get_report_data_dict(
        property.report_data['property']['data']
    )

    scalebar_names = {
        'fit': tmp_scalebar_name,
        'medium': tmp_medium_scalebar_name,
        'context': tmp_context_scalebar_name
    }

    template_input_dict = {
        'date': str(current_datetime),
        'propName': property.name,
        'acres': report_data_dict['acres'],
        'elevation': report_data_dict['elevation'],
        'legalDesc': report_data_dict['legalDesc'],
        'structFire': report_data_dict['structFire'],
        'fire': report_data_dict['fire'],
        'watershed': report_data_dict['watershed'],
        'watershedNum': report_data_dict['watershedNum'],
        'zone': report_data_dict['zone'],
        'introAerialImagery': tmp_property_name,
        'propName2': property.name,
        'aerial': tmp_aerial_name,
        'scale': scalebar_names[settings.PROPERTY_OVERVIEW_SCALE],
        'scale_aerial': scalebar_names[settings.AERIAL_SCALE],
        'scale_topo': scalebar_names[settings.TOPO_SCALE],
        'scale_hydro': scalebar_names[settings.STREAM_SCALE],
        'scale_soil': scalebar_names[settings.SOIL_SCALE],
        'directions': tmp_street_name,
        'scale_directions': scalebar_names[settings.STREET_SCALE],
        'topo': tmp_topo_name,
        'hydro': tmp_stream_name,
        'soils': tmp_soils_name,
    }

    # Create var for all soils
    soil_list = property.report_data['soils']['data']
    # Given more than 12 soil types sort them by percent area
    #   only show the 12 highest by percent area
    if len(soil_list) > 12:
        soil_list = sorted(soil_list, key=lambda x:x['percent_area'], reverse=True)
    # Add each soil to template input dict
    # Loop through each soil type
    # Use the soil_count var to match each soil type to an input in pdf
    soil_count = 1
    for soil in soil_list:
        sc_name = 'soil' + str(soil_count)
        template_input_dict[str(sc_name) + 'musym'] = soil['musym']
        template_input_dict[str(sc_name) + 'Name'] = soil['muname']
        f_acres = '{:.2f}'.format(float(soil['acres']))
        template_input_dict[str(sc_name) + 'acres'] = str(f_acres)
        template_input_dict[str(sc_name) + 'drainage'] = soil['drclssd']
        template_input_dict[str(sc_name) + 'si'] = str(soil['avgsi']) + ' ' + soil['site_index_unit']
        template_input_dict[str(sc_name) + 'erosion'] = soil['frphrtd']
        if soil['avg_rs_l']:
            f_avg_rs_l = '{:.2f}'.format(float(soil['avg_rs_l']))
        else:
            f_avg_rs_l = 'No Data'
        if soil['avg_rs_h']:
            f_avg_rs_h = '{:.2f}'.format(float(soil['avg_rs_h']))
        else:
            f_avg_rs_h = 'No Data'
        template_input_dict[str(sc_name) + 'depth'] = str(f_avg_rs_l) + ' - ' + str(f_avg_rs_h)  + ' ' + str(soil['depth_unit'])

        soil_count += 1

    rendered_pdf = template_pdf(template_input_dict)

    rendered_pdf_name = property.name + '.pdf'

    if os.path.exists(settings.PROPERTY_REPORT_PDF_DIR):
        output_pdf = os.path.join(settings.PROPERTY_REPORT_PDF_DIR,
                                  rendered_pdf_name)
        rendered_pdf.write(open(output_pdf, 'wb'))
    else:
        print('Directory does not exit')

    property_image.close()
    aerial_image.close()
    soil_image.close()
    street_image.close()
    terrain_image.close()
    stream_image.close()
    property_scalebar_image.close()
    property_context_scalebar_image.close()
    property_medium_scalebar_image.close()

    if os.path.exists(output_pdf):
        buffer = io.BytesIO()
        new_output = pypdf.PdfFileWriter()
        new_pdf = pypdf.PdfFileReader(output_pdf)
        for page in range(new_pdf.getNumPages()):
            new_output.addPage(new_pdf.getPage(page))
        new_output.write(buffer)
        # buffer.seek(0)
        return buffer.getvalue()
    else:
        raise FileNotFoundError('Failed to produce output file.')

def get_soils_data(property_geom):
    soil_area_values = {}
    equal_area_projection_id = 5070
    soil_data = []
    # get soil patches that intersect the property
    soils = SoilType.objects.filter(geometry__intersects=property_geom)
    # get the true area of the property in Acres
    property_srid = int(str(property_geom.srid))
    property_geom.transform(equal_area_projection_id)
    property_acres = sq_m_to_acres(property_geom.area)
    property_geom.transform(property_srid)

    # build dictionary of soil values for each soil type
    for soil_patch in soils:
        if not soil_patch.musym in soil_area_values.keys():
            soil_area_values[soil_patch.musym] = {
                # All SoilType fields + 2 property-specific calculated fields
                'mukey': soil_patch.mukey,
                'musym': soil_patch.musym,
                'muname': soil_patch.muname,
                'acres': 0,
                'spatial': soil_patch.spatial,
                'areasym': soil_patch.areasym,
                'shp_lng': soil_patch.shp_lng,
                'shap_ar': soil_patch.shap_ar,
                'avgsi': soil_patch.avgsi,
                'site_index_unit': 'feet',
                'drclssd': soil_patch.drclssd,
                'frphrtd': soil_patch.frphrtd,
                'avg_rs_l': cm_to_inches(soil_patch.avg_rs_l),
                'avg_rs_h': cm_to_inches(soil_patch.avg_rs_h),
                'depth_unit': 'inches',
                'percent_area': 0.0
            }
            # can't cast None to int
            if soil_patch.avgsi:
                soil_area_values[soil_patch.musym]['avgsi'] = int(soil_patch.avgsi)
        # aggregate area value
        intersection_patch = property_geom.intersection(soil_patch.geometry)
        intersection_patch.transform(equal_area_projection_id)
        soil_area_values[soil_patch.musym]['acres'] = soil_area_values[soil_patch.musym]['acres'] + sq_m_to_acres(intersection_patch.area)
        # Update the 'percent area' value
        soil_area_values[soil_patch.musym]['percent_area'] = float(soil_area_values[soil_patch.musym]['acres'])/float(property_acres)*100

    # present soil symbol values in alphanumeric order
    ordered_musyms = list(set(soil_area_values.keys()))
    ordered_musyms.sort()

    # add each soil entry in order to the output list so that order is maintained
    for musym in ordered_musyms:
        soil_data.append(soil_area_values[musym])

    return soil_data

def get_collection_from_object(source_object, geom_field, bbox):
    xmin, ymin, xmax, ymax = bbox.split(',')
    # would this be easier to read the wkt into a gpd.GeoSeries?
    feature_obj = {
        "type": "Feature",
        "properties": {},
        "geometry": json.loads(getattr(source_object, geom_field).json),
        "bbox": (xmin, ymin, xmax, ymax)
    }

    feature_collection = {
        "type": "FeatureCollection",
        "features": [feature_obj,],
        "bbox": (xmin, ymin, xmax, ymax)
    }
    return feature_collection

def get_gdf_from_features(collection):
    return gpd.GeoDataFrame.from_features(collection, crs="EPSG:%s" % settings.GEOMETRY_CLIENT_SRID)

def merge_rasters_to_img(layers, bbox, img_height=settings.REPORT_MAP_HEIGHT, img_width=settings.REPORT_MAP_WIDTH, dpi=settings.DPI):
    [xmin, ymin, xmax, ymax] = [float(x) for x in bbox.split(',')]
    bbox_array = [xmin, ymin, xmax, ymax]
    fig, ax = plt.subplots(figsize=(img_width/float(dpi),img_height/float(dpi)), dpi=dpi)
    for layer in layers:
        if layer['type'] == 'img':
            trf = transform.from_bounds(*bbox_array, width=img_width, height=img_height)
            work = show(reshape_as_raster(layer['layer']), ax=ax, transform=trf)
        else:   # 'gdf' only for now
            work = layer['layer'].plot(
                ax=ax,
                lw=layer['style']['lw'],
                ec=layer['style']['ec'],
                fc=layer['style']['fc']
            )
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    return fig2img(fig)


# Updated from https://web-backend.icare.univ-lille.fr/tutorials/convert_a_matplotlib_figure
def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    fig.canvas.draw ( )

    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = np.frombuffer ( fig.canvas.tostring_argb(), dtype=np.uint8 )
    buf.shape = ( w, h,4 )

    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = np.roll ( buf, 3, axis = 2 )
    return buf

def fig2img ( fig ):
    """
    @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
    @param fig a matplotlib figure
    @return a Python Imaging Library ( PIL ) image
    """
    # RDH: Trim off axes borders:
    fig.subplots_adjust(bottom = 0)
    fig.subplots_adjust(top = 1)
    fig.subplots_adjust(right = 1)
    fig.subplots_adjust(left = 0)

    # put the figure pixmap into a numpy array
    buf = fig2data ( fig )
    w, h, d = buf.shape
    return Image.frombytes( "RGBA", ( w ,h ), buf.tostring( ) )
