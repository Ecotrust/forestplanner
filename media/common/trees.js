$(document).ready(function() {
    init();
});

var map, controls;
var stands;
var currentStep = 1;
var steps = [undefined]; // start with a blank to make it 1-indexed

function init() {
    map = new OpenLayers.Map(
        {
            projection: new OpenLayers.Projection('EPSG:3857')
        }
    );
    var switcher = new OpenLayers.Control.LayerSwitcher({'div':OpenLayers.Util.getElement('layerswitcher')});
    map.addControl(switcher);

    map.addControl( new OpenLayers.Control.Navigation({
            dragPanOptions: {
                enableKinetic: false
            }
        }));

    map.addControl(new OpenLayers.Control.KeyboardDefaults({observeElement: 'map'}));

    map.addControl(new OpenLayers.Control.Attribution());

    map.addControl(new OpenLayers.Control.ScaleLine());

    var ghyb = new OpenLayers.Layer.Google("Google Hybrid", {type: google.maps.MapTypeId.HYBRID, 'sphericalMercator':true});
    map.addLayer(ghyb);

    var arrayAerial = [
        "http://otile1.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
        "http://otile2.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
        "http://otile3.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
        "http://otile4.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg"];
    var baseAerial = new OpenLayers.Layer.OSM("Aerial Imagery",
        arrayAerial, {attribution:"MapQuest"});
    map.addLayer(baseAerial);

    var arrayOSM = [
        "http://otile1.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
        "http://otile2.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
        "http://otile3.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
        "http://otile4.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg"];
    var baseOSM = new OpenLayers.Layer.OSM("Street Map",
        arrayOSM, {attribution:"Mapquest, OpenStreetMap"});
    map.addLayer(baseOSM);

    var esriLayers = [
      ["Topo map (Digital)", 'World_Topo_Map', 'USGS'],
      ["Topo map (Quads)", 'USA_Topo_Maps', 'USGS'],
      ["Satellite Imagery", 'World_Imagery']
    ];

    for (var i=esriLayers.length-1; i>=0; --i) {
        var lyrLongName = esriLayers[i][0];
        var lyrShortName = esriLayers[i][1];
        var attribution = "Basemaps by ESRI";
        if (esriLayers[i].length > 2) {
            attribution = attribution + ', ' + esriLayers[i][2];
        }

        var config = {
            sphericalMercator: true,
            attribution: attribution
        };

        if (esriLayers[i][0] == "Topo map (Quads)") {
            config.resolutions = [156543.03390625,78271.516953125,39135.7584765625,19567.87923828125,9783.939619140625,4891.9698095703125,2445.9849047851562,1222.9924523925781,611.4962261962891,305.74811309814453,152.87405654907226,76.43702827453613,38.218514137268066,19.109257068634033,9.554628534317017,4.777314267158508,2.388657133579254,1.194328566789627,0.5971642833948135];
            config.serverResolutions = [156543.03390625,78271.516953125,39135.7584765625,19567.87923828125,9783.939619140625,4891.9698095703125,2445.9849047851562,1222.9924523925781,611.4962261962891,305.74811309814453,152.87405654907226,76.43702827453613,38.218514137268066,19.109257068634033,9.554628534317017,4.777314267158508];
        }

        var lyr = new OpenLayers.Layer.XYZ( lyrLongName,
            "http://server.arcgisonline.com/ArcGIS/rest/services/"+ lyrShortName +"/MapServer/tile/${z}/${y}/${x}",
            config
        );
        lyr.shortName = lyrShortName;
        map.addLayer(lyr); 
    }

    var tileServerLayers = [
        [ "Wetlands", "LOT_wetlands"],
        [ "Stream Buffers", "LOT_streambuffers"],
        [ "Streams", "LOT_streams"]
    ];

    for (var i=tileServerLayers.length-1; i>=0; --i) {
        var lyrLongName = tileServerLayers[i][0];
        var lyrShortName = tileServerLayers[i][1];
        var arrayTile = [
            "http://a.tiles.ecotrust.org/tiles/" + lyrShortName + "/${z}/${x}/${y}.png",
            "http://b.tiles.ecotrust.org/tiles/" + lyrShortName + "/${z}/${x}/${y}.png",
            "http://c.tiles.ecotrust.org/tiles/" + lyrShortName + "/${z}/${x}/${y}.png",
            "http://d.tiles.ecotrust.org/tiles/" + lyrShortName + "/${z}/${x}/${y}.png",
        ];
        var lyr = new OpenLayers.Layer.XYZ( lyrLongName, arrayTile,
            {sphericalMercator: true, isBaseLayer: false, visibility: false, attribution:"Ecotrust"}
        );
        lyr.shortName = lyrShortName;
        map.addLayer(lyr);
        lyr.events.register('visibilitychanged', lyr, function(evt) {
            if (this.visibility) {
                $('#legend').append('<div id="' + this.shortName + '-legend">' +
                    '<img src="/media/img/legends/' + this.shortName + '.png">');
            } else {
                $('#' + this.shortName + '-legend').remove();
            }
        });
    }

    var soils = new OpenLayers.Layer.XYZ( "Soil Types (Names)",
        "http://server.arcgisonline.com/ArcGIS/rest/services/Specialty/Soil_Survey_Map/MapServer/tile/${z}/${y}/${x}",
        {sphericalMercator: true,
         isBaseLayer: false,
         visibility: false,
         opacity: 0.75,
         attribution: "ESRI, USDA NRCS"} 
    );
    map.addLayer(soils);
    soils.events.register('visibilitychanged', soils, function(evt) {
        if (soils.visibility) {
            $('.layersDiv').append('<div id="soil-legend" style="text-align:center;"><img src="/media/img/soil_legend.png"><br><a target="_blank" href="http://goto.arcgisonline.com/maps/Specialty/Soil_Survey_Map">more info</a></div>');
        } else {
            $('#soil-legend').remove();
        }
    });

     var soilsWMS = new OpenLayers.Layer.WMS( "Soil Types (Codes)",
        "http://sdmdataaccess.nrcs.usda.gov/Spatial/SDM.wms",
        {
            layers: 'MapunitPoly',
            transparent: true
        }
        , {
            isBaseLayer: false,
            attribution: "USDA NRCS",
            visibility: false
        }
    );
    map.addLayer(soilsWMS);

    var tileServerLayers2 = [
        [ "Conservation Easements", "LOT_natconseasedb"],
        [ "Critical Habitat (Public Land)", "Crithab"],
        [ "Critical Stream Habitat", "Crithab_streams"],
        [ "Land Ownership", "LOT_protareas"],
        [ "Mill Facilities", "USFSMillFacilities", "USFS"],
        [ "Watershed Boundaries", "LOT_watersheds"],
        [ "Counties", "LOT_counties"],
        [ "Township and Range", "LOT_plss"],
        [ "Tax Lots (where available)", "LOT_parcels"],
        [ "Steep Slopes (>40%)", "LOT_steepslopes"]
    ];

    for (var i=tileServerLayers2.length-1; i>=0; --i) {
        var lyrLongName = tileServerLayers2[i][0];
        var lyrShortName = tileServerLayers2[i][1];
        var arrayTile = [
            "http://a.tiles.ecotrust.org/tiles/" + lyrShortName + "/${z}/${x}/${y}.png",
            "http://b.tiles.ecotrust.org/tiles/" + lyrShortName + "/${z}/${x}/${y}.png",
            "http://c.tiles.ecotrust.org/tiles/" + lyrShortName + "/${z}/${x}/${y}.png",
            "http://d.tiles.ecotrust.org/tiles/" + lyrShortName + "/${z}/${x}/${y}.png",
        ];
        var attribution = "Ecotrust"
        if (tileServerLayers2[i].length > 2){
            attribution = tileServerLayers2[i][2];
        }
        var lyr = new OpenLayers.Layer.XYZ( lyrLongName, arrayTile,
            {sphericalMercator: true, isBaseLayer: false, visibility: false, attribution:attribution}
        );
        lyr.shortName = lyrShortName;
        map.addLayer(lyr);
        lyr.events.register('visibilitychanged', lyr, function(evt) {
            if (this.visibility) {
                $('#legend').append('<div id="' + this.shortName + '-legend">' +
                    '<img src="/media/img/legends/' + this.shortName + '.png">');
            } else {
                $('#' + this.shortName + '-legend').remove();
            }
        });
    }

    map.setCenter(new OpenLayers.LonLat(0, 0), 7);

    for (var i=map.layers.length-1; i>=0; --i) {
        map.layers[i].animationEnabled = true;
    }

    app.markers = new OpenLayers.Layer.Markers("search", {displayInLayerSwitcher: false});               
    map.addLayer(app.markers);

    // Add stands
    var renderer = OpenLayers.Util.getParameters(window.location.href).renderer;
    app.renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;

    new_features = new OpenLayers.Layer.Vector("New Features", {
        renderers: app.renderer, 
        styleMap: map_styles.drawn,
        displayInLayerSwitcher: false
    }
    );
    map.addLayer(new_features);
    app.new_features = new_features;
    

    app.geojson_format = new OpenLayers.Format.GeoJSON(),
    app.property_layer = new OpenLayers.Layer.Vector("My Properties",  {
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

