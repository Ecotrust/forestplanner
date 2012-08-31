$(document).ready(function() {
    init();
});

var map, controls;
var stands;
var currentStep = 1;
var steps = [undefined]; // start with a blank to make it 1-indexed

function init() {
    map = new OpenLayers.Map();
    var switcher = new OpenLayers.Control.LayerSwitcher();
    map.addControl(switcher);

    map.addControl(new OpenLayers.Control.Navigation({
            dragPanOptions: {
                enableKinetic: false
            }
        }));

    map.addControl(new OpenLayers.Control.Attribution());

    //map.addControl(new OpenLayers.Control.Zoom());
    

    var gphy = new OpenLayers.Layer.Google( "Google Physical", {type: google.maps.MapTypeId.TERRAIN});
    var ghyb = new OpenLayers.Layer.Google( "Google Hybrid", {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 21});
    var gsat = new OpenLayers.Layer.Google( "Google Satellite", {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22});
    var arrayOSM = ["http://otile1.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
                "http://otile2.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
                "http://otile3.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
                "http://otile4.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg"];

    var arrayMapboxTerrain = [
        "http://a.tiles.mapbox.com/v3/examples.map-4l7djmvo/${z}/${x}/${y}.png",
        "http://b.tiles.mapbox.com/v3/examples.map-4l7djmvo/${z}/${x}/${y}.png",
        "http://c.tiles.mapbox.com/v3/examples.map-4l7djmvo/${z}/${x}/${y}.png"];

    var arrayAerial = ["http://oatile1.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
                    "http://oatile2.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
                    "http://oatile3.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
                    "http://oatile4.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg"];

    var baseAerial = new OpenLayers.Layer.OSM("MapQuest Open Aerial", arrayAerial);
    var baseOSM = new OpenLayers.Layer.OSM("Mapbox OSM Terrain", arrayMapboxTerrain);
    var nhd = new OpenLayers.Layer.XYZ( "EPA NHD",
        "http://watersgeo.epa.gov/ARCGIS/REST/services/OW/NHD_Med_Detailed_WMERC/MapServer/tile/${z}/${y}/${x}",
        //"/tile/${z}/${y}/${x}",
        {sphericalMercator: true, isBaseLayer: false, visibility: false, opacity: 0.75} 
    );
    var huc = new OpenLayers.Layer.XYZ( "EPA HUCs",
        //"/tile/${z}/${y}/${x}",
        "http://watersgeo.epa.gov/ArcGIS/rest/services/OW/WBD_WMERC/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true, isBaseLayer: false, visibility: false} 
    );
    var soils = new OpenLayers.Layer.XYZ( "Soil Survey Map",
        //"/tile/${z}/${y}/${x}",
        "http://server.arcgisonline.com/ArcGIS/rest/services/Specialty/Soil_Survey_Map/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true, isBaseLayer: false, visibility: false, opacity: 0.75} 
    );

    /* 
     * TODO legend for soils data
     * http://server.arcgisonline.com/ArcGIS/rest/services/Specialty/Soil_Survey_Map/MapServer/legend
     *
     * TODO query for soils data
     * http://server.arcgisonline.com/ArcGIS/rest/services/Specialty/Soil_Survey_Map/MapServer/1/query?f=json&returnGeometry=true&spatialRel=esriSpatialRelIntersects&geometry=%7B%22xmin%22%3A-13673363.281068286%2C%22ymin%22%3A6024153.000358967%2C%22xmax%22%3A-13669694.3037106%2C%22ymax%22%3A6027821.977716654%2C%22spatialReference%22%3A%7B%22wkid%22%3A102100%7D%7D&geometryType=esriGeometryEnvelope&inSR=102100&outFields=*&outSR=102100&callback=dojo.io.script.jsonp_dojoIoScript20._jsonpCallback
     * http://server.arcgisonline.com/ArcGIS/rest/services/Specialty/Soil_Survey_Map/MapServer/0/query?f=json&returnGeometry=true&spatialRel=esriSpatialRelIntersects&geometry=%7B%22xmin%22%3A-13635374.078010553%2C%22ymin%22%3A5702238.455736051%2C%22xmax%22%3A-13634456.833671134%2C%22ymax%22%3A5703155.700075472%2C%22spatialReference%22%3A%7B%22wkid%22%3A102100%7D%7D&geometryType=esriGeometryEnvelope&inSR=102100&outFields=*&outSR=102100&callback=dojo.io.script.jsonp_dojoIoScript28._jsonpCallback
     */

    var esri_base = new OpenLayers.Layer.XYZ( "ESRI Topo Maps",
        /*
        ESRI_Imagery_World_2D (MapServer)
        ESRI_StreetMap_World_2D (MapServer)
        NatGeo_World_Map (MapServer)
        NGS_Topo_US_2D (MapServer)
        Ocean_Basemap (MapServer)
        USA_Topo_Maps (MapServer)
        World_Imagery (MapServer)
        World_Physical_Map (MapServer)
        World_Shaded_Relief (MapServer)
        World_Street_Map (MapServer)
        World_Terrain_Base (MapServer)
        World_Topo_Map (MapServer)
        */
        "http://server.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true} 
    );

    var apiKey = "AhYe6O-7ejQ1fsFbztwu7PScwp2b1U1vM47kArB_8P2bZ0jiyJua2ssOLrU4pH70";

    var road = new OpenLayers.Layer.Bing({
        name: "Bing Road",
        key: apiKey,
        type: "Road"
    });
    var hybrid = new OpenLayers.Layer.Bing({
        name: "Bing Hybrid",
        key: apiKey,
        type: "AerialWithLabels"
    });
    var aerial = new OpenLayers.Layer.Bing({
        name: "Bing Aerial",
        key: apiKey,
        type: "Aerial"
    });

    map.addLayers([hybrid, road]);
    map.addLayers([ghyb, gphy]);
    map.addLayer(baseAerial);
    map.addLayer(esri_base);
    map.addLayer(baseOSM);
    map.addLayer(soils);
    map.addLayer(nhd);
    map.addLayer(huc);

    for (var i=map.layers.length-1; i>=0; --i) {
        map.layers[i].animationEnabled = true;
    }


    app.markers = new OpenLayers.Layer.Markers("search", {displayInLayerSwitcher: false});               
    map.addLayer(app.markers);

    // Add stands
    var renderer = OpenLayers.Util.getParameters(window.location.href).renderer;
    app.renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;

    new_features = new OpenLayers.Layer.Vector("New Features", 
            {
                renderers: app.renderer, 
                styleMap: map_styles.drawn,
                displayInLayerSwitcher: false
            }
    );
    map.addLayer(new_features);
    app.new_features = new_features;
    

    app.geojson_format = new OpenLayers.Format.GeoJSON(),
    app.property_layer = new OpenLayers.Layer.Vector("Properties",  {
                renderers: app.renderer, 
                styleMap: map_styles.forestProperty
            });
    map.addLayer(app.property_layer);

    // add controls, save references
    app.selectFeature = new OpenLayers.Control.SelectFeature(app.property_layer,
        { "clickout": false});
    
    // reenable click and drag in vectors
    app.selectFeature.handlers.feature.stopDown = false; 
    
    map.addControl(app.selectFeature);
    app.modifyFeature = new OpenLayers.Control.ModifyFeature(app.property_layer);
    map.addControl(app.modifyFeature);
    // draw is in tree.js TODO: move)
    // activate select now
    app.selectFeature.activate();
  
    new_snap = new OpenLayers.Control.Snapping({
                layer: app.new_features,
                targets: [app.property_layer],
                greedy: false
            });
    new_snap.activate();
    existing_snap = new OpenLayers.Control.Snapping({
                layer: app.property_layer,
                targets: [app.property_layer],
                greedy: false
            });
    existing_snap.activate();

    draw = new OpenLayers.Control.DrawFeature(new_features, OpenLayers.Handler.Polygon);
    map.addControl(draw);
    app.drawFeature = draw;

    // new app methods
    app.cleanupForm = function ($form) {
      // remove the submit button, strip out the geometry
      $form
        .find('input:submit').remove().end()
        .find('#id_geometry_final').closest('.field').remove();

      // put the form in a well and focus the first field
      $form.addClass('well');
      $form.find('.field').each(function () {
        var $this = $(this);
        // add the bootstrap classes
        $this.addClass('control-group');
        $this.find('label').addClass('control-label');
        $this.find('input').wrap($('<div/>', { "class": "controls"}));
        $this.find('.controls').append($('<p/>', { "class": "help-block"}));

      });
      $form.find('input:visible').first().focus();
    };
} //end init

