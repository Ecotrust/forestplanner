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

    var gphy = new OpenLayers.Layer.Google( "Google Physical", {type: google.maps.MapTypeId.TERRAIN});
    var ghyb = new OpenLayers.Layer.Google( "Google Hybrid", {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 21});
    var gsat = new OpenLayers.Layer.Google( "Google Satellite", {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22});

    var arrayMapboxTerrain = [
        "http://a.tiles.mapbox.com/v3/examples.map-4l7djmvo/${z}/${x}/${y}.jpg",
        "http://b.tiles.mapbox.com/v3/examples.map-4l7djmvo/${z}/${x}/${y}.jpg",
        "http://c.tiles.mapbox.com/v3/examples.map-4l7djmvo/${z}/${x}/${y}.jpg"];

    var arrayAerial = [
        "http://oatile1.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
        "http://oatile2.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
        "http://oatile3.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
        "http://oatile4.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg"];

    /* Mapquest OSM
    var arrayOSM = [
        "http://otile1.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
        "http://otile2.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
        "http://otile3.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
        "http://otile4.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg"];
    */

    var baseAerial = new OpenLayers.Layer.OSM("MapQuest Open Aerial", arrayAerial, {attribution:"MapQuest"});
    var baseOSM = new OpenLayers.Layer.OSM("Mapbox OSM Terrain", arrayMapboxTerrain, {attribution:"Mapbox"});
    var esri_base = new OpenLayers.Layer.XYZ( "ESRI Topo Maps",
        "http://server.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer/tile/${z}/${y}/${x}",
        {
            sphericalMercator: true,
            attribution: "ESRI, (c) 2011 National Geographic Society, I-Cubed"
        } 
    );

    var bingApiKey = "AhYe6O-7ejQ1fsFbztwu7PScwp2b1U1vM47kArB_8P2bZ0jiyJua2ssOLrU4pH70";
    var road = new OpenLayers.Layer.Bing({
        name: "Bing Road",
        key: bingApiKey,
        type: "Road"
    });
    var hybrid = new OpenLayers.Layer.Bing({
        name: "Bing Hybrid",
        key: bingApiKey,
        type: "AerialWithLabels"
    });
    var aerial = new OpenLayers.Layer.Bing({
        name: "Bing Aerial",
        key: bingApiKey,
        type: "Aerial"
    });

    tileServerLayers = [
        [ "Streams", "LOT_streams"],
        [ "Watersheds", "LOT_watersheds"],
        [ "Conservation Easements", "LOT_natconseasedb"],
        [ "Critical Stream Habitat", "Crithab_streams"], 
        [ "Wetlands", "LOT_wetlands"],
        [ "Protected Areas", "LOT_protareas"],
        [ "PLSS", "LOT_plss"],
        [ "USFS Mill Facilities", "USFSMillFacilities"],
        [ "Critical Habitat", "Crithab"],
        [ "Counties", "LOT_counties"]
    ];

    map.addLayers([hybrid, road]);
    map.addLayer(baseOSM);
    map.addLayers([ghyb, gphy]);
    map.addLayer(baseAerial);
    map.addLayer(esri_base);

    for (var i=tileServerLayers.length-1; i>=0; --i) {
        var lyrLongName = tileServerLayers[i][0];
        var lyrShortName = tileServerLayers[i][1];
        var lyr = new OpenLayers.Layer.XYZ( lyrLongName, 
            "http://54.214.12.22/tiles/" + lyrShortName + "/${z}/${x}/${y}.png",
            {sphericalMercator: true, isBaseLayer: false, visibility: false, attribution:"Ecotrust"} 
        );
        lyr.shortName = lyrShortName;
        map.addLayer(lyr);
        lyr.events.register('visibilitychanged', lyr, function(evt) {
            if (this.visibility) {
                $('.layersDiv').append('<div id="' + this.shortName + '-legend" style="text-align:center;">' + 
                    '<img src="/media/img/legends/' + this.shortName + '.png">');
            } else {
                $('#' + this.shortName + '-legend').remove();
            }
        });
    }

    var soils = new OpenLayers.Layer.XYZ( "Soil Survey",
        "http://server.arcgisonline.com/ArcGIS/rest/services/Specialty/Soil_Survey_Map/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true, 
         isBaseLayer: false, 
         visibility: false, 
         opacity: 0.75,
         attribution: "ESRI, USDA Natural Resources Conservation Service"} 
    );
    map.addLayer(soils);
    soils.events.register('visibilitychanged', soils, function(evt) {
        if (soils.visibility) {
            $('.layersDiv').append('<div id="soil-legend" style="text-align:center;"><img src="/media/img/soil_legend.png"><br><a target="_blank" href="http://goto.arcgisonline.com/maps/Specialty/Soil_Survey_Map">more info</a></div>');
        } else {
            $('#soil-legend').remove();
        }
    });

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
    app.stand_layer = new OpenLayers.Layer.Vector("Stands",  {
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

    // 
    // Snapping control for drawing properties
    //
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

