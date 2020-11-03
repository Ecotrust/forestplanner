import os, io, datetime, requests, json, decimal
from datetime import date
from django.conf import settings
from django.contrib.humanize.templatetags import humanize
from landmapper.models import SoilType
from landmapper.fetch import soils_from_nrcs
from landmapper.map_layers import views as map_views
from pdfjinja import PdfJinja
import PyPDF2 as pypdf
from tempfile import NamedTemporaryFile

def get_property_report(property, taxlots):
    # TODO: call this in "property" after creating the object instance

    # calculate orientation, w x h, bounding box, centroid, and zoom level
    property_specs = get_property_specs(property)
    property_layer = map_views.get_property_image_layer(
        property, property_specs)
    # TODO (Sara is creating the layer now)
    taxlot_layer = map_views.get_taxlot_image_layer(property_specs)

    aerial_layer = map_views.get_aerial_image_layer(property_specs)
    street_layer = map_views.get_street_image_layer(property_specs)
    topo_layer = map_views.get_topo_image_layer(property_specs)
    soil_layer = map_views.get_soil_image_layer(property_specs)
    stream_layer = map_views.get_stream_image_layer(property_specs)

    property.property_map_image = map_views.get_property_map(
        property_specs, base_layer=aerial_layer, property_layer=property_layer)
    property.aerial_map_image = map_views.get_aerial_map(
        property_specs,
        base_layer=aerial_layer,
        lots_layer=taxlot_layer,
        property_layer=property_layer)
    property.street_map_image = map_views.get_street_map(
        property_specs,
        base_layer=street_layer,
        lots_layer=taxlot_layer,
        property_layer=property_layer)
    property.terrain_map_image = map_views.get_terrain_map(
        property_specs, base_layer=topo_layer, property_layer=property_layer)
    if settings.STREAMS_BASE_LAYER == 'aerial':
        stream_base_layer = aerial_layer
    else:
        stream_base_layer = topo_layer
    property.stream_map_image = map_views.get_stream_map(
        property_specs,
        base_layer=stream_base_layer,
        stream_layer=stream_layer,
        property_layer=property_layer)
    property.soil_map_image = map_views.get_soil_map(
        property_specs,
        base_layer=aerial_layer,
        lots_layer=taxlot_layer,
        soil_layer=soil_layer,
        property_layer=property_layer)
    property.scalebar_image = map_views.get_scalebar_image(property_specs,
                                                           span_ratio=0.75)

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
        acres.append(taxlot.acres)
        min_elevation.append(taxlot.min_elevation)
        max_elevation.append(taxlot.max_elevation)
        legal.append("%s%s %s" %
                     (taxlot.twnshpdir, taxlot.frstdivno, taxlot.twnshplab))
        agency.append(taxlot.agency)
        odf_fpd.append(taxlot.odf_fpd)
        name.append(taxlot.name)
        huc12.append(taxlot.huc12)
        orzdesc.append(taxlot.orzdesc)
        # twnshpno.append(taxlot.twnshpno)
        # rangeno.append(taxlot.rangeno)
        # frstdivno.append(taxlot.frstdivno)

    min_elevation = pretty_print_float(aggregate_min(min_elevation))
    max_elevation = pretty_print_float(aggregate_max(max_elevation))

    if not min_elevation == None and not max_elevation == None:
        elevation_label = 'Elevation Range'
        elevation_value = "%s - %s ft" % (pretty_print_float(m_to_ft(min_elevation)),pretty_print_float(m_to_ft(max_elevation)))
    else:
        elevation_label = 'Elevation'
        elevation_value = 'Unknown'

    return [
        ['Acres',
         pretty_print_float(sq_ft_to_acres(aggregate_sum(acres)))],
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
        'zoom':
        None  # {'lat': (EPSG:4326 float), 'lon': (EPSG:4326 float), 'zoom': float}
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
    scalebar_url = settings.APP_URL + '/report/' + property_id + '/scalebar'

    property_image = requests.get(property_url, stream=True)
    aerial_image = requests.get(aerial_url, stream=True)
    street_image = requests.get(street_url, stream=True)
    terrain_image = requests.get(terrain_url, stream=True)
    stream_image = requests.get(stream_url, stream=True)
    soil_image = requests.get(soil_types_url, stream=True)
    property_scalebar_image = requests.get(scalebar_url, stream=True)

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
        property.report_data['property']['data'])

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
        'scale': tmp_scalebar_name,
        'scale_aerial': tmp_scalebar_name,
        'scale_topo': tmp_scalebar_name,
        'scale_hydro': tmp_scalebar_name,
        'scale_soil': tmp_scalebar_name,
        'directions': tmp_street_name,
        'scale_directions': tmp_scalebar_name,
        'topo': tmp_topo_name,
        'hydro': tmp_stream_name,
        'soils': tmp_soils_name,
    }

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
