$(document).ready(function() {
    init();
});

var map, controls;
var stands;
var currentStep = 1;
var steps = [undefined]; // start with a blank to make it 1-indexed

function init() {
    map = new OpenLayers.Map('map');
    var switcher = new OpenLayers.Control.LayerSwitcher({
        'div': OpenLayers.Util.getElement('tab_data'),
        'roundedCorner': false,
        'displayClass': 'mylayer'
    });
    map.addControl(switcher);

    var gphy = new OpenLayers.Layer.Google( "Google Physical", {type: google.maps.MapTypeId.TERRAIN});
    var ghyb = new OpenLayers.Layer.Google( "Google Hybrid", {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 20});
    var gsat = new OpenLayers.Layer.Google( "Google Satellite", {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22});

    var arrayOSM = ["http://otile1.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
                "http://otile2.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
                "http://otile3.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg",
                "http://otile4.mqcdn.com/tiles/1.0.0/osm/${z}/${x}/${y}.jpg"];
    var arrayAerial = ["http://oatile1.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
                    "http://oatile2.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
                    "http://oatile3.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
                    "http://oatile4.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg"];
    
    var baseOSM = new OpenLayers.Layer.OSM("MapQuest-OSM Tiles", arrayOSM);
    var baseAerial = new OpenLayers.Layer.OSM("MapQuest Open Aerial Tiles", arrayAerial);

    map.addLayers([gsat, gphy, ghyb]);
    map.addLayer(baseOSM);
    map.addLayer(baseAerial);

    map.setCenter(new OpenLayers.LonLat(-124.38, 42.8).transform(
        new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject()), 13);
    
    for (var i=map.layers.length-1; i>=0; --i) {
        map.layers[i].animationEnabled = false;
    };

    // Add stands
    var renderer = OpenLayers.Util.getParameters(window.location.href).renderer;
    renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;
    var new_styles = new OpenLayers.StyleMap({
        "default": new OpenLayers.Style(null, {
            rules: [
                new OpenLayers.Rule({
                    symbolizer: {
                        "Polygon": {
                            fillColor: "green",
                            fillOpacity: 0.25,
                            strokeWidth: 1,
                            strokeOpacity: 1,
                            strokeColor: "#44ff00"
                        },
                    }
                })
            ]
        }),
        "select": new OpenLayers.Style({
            fillColor: "#44ff00",
            strokeOpacity: 1,
            strokeColor: "#ffcc00"
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
    // var styles = new OpenLayers.StyleMap({
    //     "default": new OpenLayers.Style(null, {
    //         rules: [
    //             new OpenLayers.Rule({
    //                 symbolizer: {
    //                     "Polygon": {
    //                         fillColor: "#00ccff",
    //                         fillOpacity: 0.25,
    //                         strokeWidth: 0.25,
    //                         strokeOpacity: 1,
    //                         strokeColor: "white"
    //                     }
    //                 }
    //             })
    //         ]
    //     }),
    //     "select": new OpenLayers.Style({
    //         fillColor: "#ffcc00",
    //         strokeOpacity: 1,
    //         strokeColor: "#ffcc00"
    //     }),
    //     "temporary": new OpenLayers.Style(null, {
    //         rules: [
    //             new OpenLayers.Rule({
    //                 symbolizer: {
    //                     "Point": {
    //                         pointRadius: 5,
    //                         fillColor: "#ffcc00",
    //                     },
    //                     "Polygon": {
    //                         pointRadius: 5,
    //                         fillColor: "white",
    //                         fillOpacity: 0.25,
    //                         strokeWidth: 1,
    //                         strokeOpacity: 1,
    //                         strokeColor: "#ffcc00"
    //                     },
    //                 }
    //             })
    //         ]
    //     })
    // });
    // stands = new OpenLayers.Layer.Vector("Stands", 
    //         {
    //             renderers: renderer, 
    //             styleMap: styles,
    //         }
    // );
    // stands.events.on({
    //     'beforefeaturemodified': function(evt) {
    //         console.log("Selected " + evt.feature.id  + " for modification");
    //     },
    //     'afterfeaturemodified': function(evt) {
    //         console.log("Finished with " + evt.feature.id);
    //     }
    // });
    // map.addLayer(stands);

    new_features = new OpenLayers.Layer.Vector("New Features", 
            {
                renderers: renderer, 
                styleMap: new_styles,
            }
    );
    map.addLayer(new_features);

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
    var featureCallback = function(f) { 
        draw.deactivate();
        app.saveFeature(f);
    };
    draw.featureAdded = featureCallback;
    map.addControl(draw);

    app.draw = draw;
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

}; //end init

