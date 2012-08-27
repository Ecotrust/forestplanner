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
    map.addLayer(baseAerial);
    map.addLayer(baseOSM);
    map.addLayer(soils);
    map.addLayer(nhd);
    map.addLayer(huc);
    map.addLayers([gsat, gphy, ghyb]);

    for (var i=map.layers.length-1; i>=0; --i) {
        map.layers[i].animationEnabled = true;
    };


    app.markers = new OpenLayers.Layer.Markers("search", {displayInLayerSwitcher: false});               
    map.addLayer(app.markers);

    // Add stands
    var renderer = OpenLayers.Util.getParameters(window.location.href).renderer;
    app.renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;
    app.new_styles = new OpenLayers.StyleMap({
        "default": new OpenLayers.Style(null, {
            rules: [
                new OpenLayers.Rule({
                    symbolizer: {
                        "Polygon": {
                            fillColor: "white",
                            fillOpacity: 0.25,
                            strokeWidth: 1,
                            strokeOpacity: 1,
                            strokeColor: "darkgrey",
                        },
                    }
                })
            ]
        }),
        "select": new OpenLayers.Style({
            fillColor: "lightgreen",
            strokeOpacity: 1,
            strokeColor: "#44ff00"
        }),
        "temporary": new OpenLayers.Style(null, {
            rules: [
                new OpenLayers.Rule({
                    symbolizer: {
                        "Point": {
                            pointRadius: 5,
                            fillColor: "#44ff00",
                        },
                        "Polygon": {
                            pointRadius: 5,
                            fillColor: "white",
                            fillOpacity: 0.25,
                            strokeWidth: 1,
                            strokeOpacity: 1,
                            strokeColor: "#44ff00"
                        },
                    }
                })
            ]
        })
    });

    
    new_features = new OpenLayers.Layer.Vector("New Features", 
            {
                renderers: app.renderer, 
                styleMap: app.new_styles,
                displayInLayerSwitcher: false
            }
    );
    map.addLayer(new_features);
    app.new_features = new_features;
    

    app.geojson_format = new OpenLayers.Format.GeoJSON(),
    app.property_layer = new OpenLayers.Layer.Vector("Properties",  {
                renderers: app.renderer, 
                styleMap: app.new_styles,
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
    // var modify = new OpenLayers.Control.ModifyFeature(stands);
    // map.addControl(modify);

    // var selector = new OpenLayers.Control.SelectFeature(stands);
    // var selectCallback = function(f){ 
    //     $('div#stand-selected').show();
    //     console.log(f);
    //     var x = "<div><table><tr><th>Stand Id</th><td>" + f.attributes['id'] + "</td></tr>";
    //     x += "<tr><th>Silvicultural Prescription</th><td>Shelterwood</td></tr>";
    //     x += "<tr><th>Dominant Species</th><td>Douglas Fir</td></tr>";
    //     x += "</table></div>";
    //     $('div#stand-info').html(x);
    // };
    // selector.onSelect = selectCallback;
    // map.addControl(selector);

    draw = new OpenLayers.Control.DrawFeature(new_features, OpenLayers.Handler.Polygon);
   
    map.addControl(draw);

    app.drawFeature = draw;
    
    // $('input#confirm-save-stand').click( function(e) {
    //     e.preventDefault();
    //     fs = new_stands.features;
    //     if (fs.length != 1) {
    //         alert("error: need exactly one new stand");
    //         console.log(fs);
    //     }
    //     wkt = fs[0].geometry.toString();
    //     $.ajax({
    //         url: "/trees/stand/", 
    //         type: 'POST',
    //         data: { 'wkt': wkt }, 
    //         success: function(data) {
    //             alert(data);
    //             stands.addFeatures(geojson_format.read(data));
    //         },
    //         dataType: 'json',
    //         async: true
    //     })
    //     .error( function(e) { 
    //         console.log(e);
    //         alert("An error occured trying to record stand data... Please try again."); 
    //         continue_steps = false;
    //     });
    // });

    // $('a#pill-create-stand').click(function(e) {
    //     modify.deactivate();
    //     selector.unselectAll();
    //     selector.deactivate();
    //     draw.activate();
    // });
    // $('a#pill-select-stand').click(function(e) {
    //     $('div#stand-selected').hide();
    //     modify.deactivate();
    //     selector.activate();
    //     draw.deactivate();
    // });
    // $('a#pill-navigate').click(function(e) {
    //     modify.deactivate();
    //     selector.unselectAll();
    //     selector.deactivate();
    //     draw.deactivate();
    // });

    // $('.cancel-stand').click(function(e) {
    //     new_stands.removeAllFeatures();
    //     $('div#stand-form-container').hide();
    //     draw.activate();
    // });

    // // Ctl-Z to undo, Ctl-Y to redo, Esc to cancel
    // OpenLayers.Event.observe(document, "keydown", function(evt) {
    //     var handled = false;
    //     switch (evt.keyCode) {
    //         case 90: // z
    //             if (evt.metaKey || evt.ctrlKey) {
    //                 draw.undo();
    //                 handled = true;
    //             }
    //             break;
    //         case 89: // y
    //             if (evt.metaKey || evt.ctrlKey) {
    //                 draw.redo();
    //                 handled = true;
    //             }
    //             break;
    //         case 27: // esc
    //             draw.cancel();
    //             handled = true;
    //             break;
    //     }
    //     if (handled) {
    //         OpenLayers.Event.stop(evt);
    //     }
    // });

    // // configure the snapping agent
    // var snap = new OpenLayers.Control.Snapping({
    //     layer: new_stands,
    //     targets: [stands, new_stands],
    //     defaults: {
    //         nodeTolerance: 10,
    //         vertexTolerance: 10,
    //         edgeTolerance: 3 
    //     },
    //     greedy: true
    // });
    // map.addControl(snap);
    // snap.activate();

    // var geojson_format = new OpenLayers.Format.GeoJSON();
    // $.ajax({
    //     url: "/trees/stands_json/", 
    //     type: 'GET',
    //     success: function(data) {
    //         stands.addFeatures(geojson_format.read(data));
    //     },
    //     dataType: 'json',
    //     async: true
    // })
    // .error( function(e) { 
    //     console.log(e);
    //     alert("An error occured trying to record stand data... Please try again."); 
    //     continue_steps = false;
    // });

    // $('#panel').modal({ backdrop: true });
    // $('.load-in-panel').live('click', function(e) {
    //         e.preventDefault();
    //         var url = $(e.target).attr('href');
    //         $.get(url, function(data) {
    //             $('#panel').empty();
    //             $('<div><div class="modal-header"><a href="#" class="close" data-dismiss="modal">x</a><h3>Forest Scenario Planner</h3></div><div class="modal-body">' + data + '</div></div>').appendTo('#panel');
    //             $('#panel').modal('show');
    //         });
                            
    // });


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
      
    }
}; //end init

