var timemap1 = new OpenLayers.Map();
var timemap2 = new OpenLayers.Map();
var standScenario1;
var standScenario2;
var updatingMap1 = false;
var updatingMap2 = false;
var timemapInitialized = false;
var selectedTimeMapMetric = 'carbon';
var timemapScenarioData = {};
var timemapBreaks = [4,8,12,16]; 

var initTimeMap = function() {
    timemap1.render("timemap1");
    timemap2.render("timemap2");

    var bounds = app.properties.viewModel.selectedProperty().feature.geometry.bounds;
    if (!bounds)
        bounds = OpenLayers.Bounds.fromArray([-13954802.50397, 5681411.4375898, -13527672.389972, 5939462.8450446]);

    timemap1.zoomToExtent(bounds);
    timemap2.zoomToExtent(bounds);

    var c1, c2, z1, z2;
    timemap1.events.register("moveend", timemap1, function() {
            if(!updatingMap2){
                c1 = this.getCenter();
                z1 = this.getZoom();
                updatingMap1 = true;
                timemap2.panTo(c1);
                timemap2.zoomTo(z1);
                updatingMap1 = false;
            }
    });
    timemap2.events.register("moveend", timemap2, function() {
            if(!updatingMap2){
                c2 = this.getCenter();
                z2 = this.getZoom();
                updatingMap2 = true;
                timemap1.panTo(c2);
                timemap1.zoomTo(z2);
                updatingMap2 = false;
            }
    });       
    timemapInitialized = true;
};


var refreshTimeMap = function (f1, f2) {

    if (!timemapInitialized)
        initTimeMap();

    selectedTimeMapMetric = $("#timemap-metrics-select").find(":selected").val();
    if (!selectedTimeMapMetric || !(selectedTimeMapMetric in chartMetrics)) {
        console.log("WARNING: no metric selected. Defaulting to 'carbon'");
        selectedTimeMapMetric = 'carbon';
    }

    if (f1) {
        standScenario1.removeAllFeatures();
        $("#error-timemap1").fadeOut();
        var opt = $('#select-scenario1').find(":selected").val();
        var data = timemapScenarioData[opt];
        if (data) {
            // we have it already
            standScenario1.addFeatures(app.geojson_format.read(data));
        } else {
            // go fetch it 
            var geojson_url = "/features/generic-links/links/geojson/trees_scenario_" + opt +"/";
            $.get( geojson_url, function(data) {
                if (data.features.length) {
                    standScenario1.addFeatures(app.geojson_format.read(data));
                    timemapScenarioData[opt] = data;
                    processBreaks();
                    standScenario1.redraw();
                } else {
                    console.log("First scenario doesn't have any features! Check scenariostands...")
                    $("#error-timemap1").fadeIn();
                }
            });
        }
    }

    if (f2) {
        standScenario2.removeAllFeatures();
        $("#error-timemap2").fadeOut();
        var opt2 = $('#select-scenario2').find(":selected").val();

        var data = timemapScenarioData[opt2];
        if (data) {
            // we have it already
            standScenario2.addFeatures(app.geojson_format.read(data));
        } else {
            // go fetch it 
            var geojson_url2 = "/features/generic-links/links/geojson/trees_scenario_" + opt2 +"/";
            $.get( geojson_url2, function(data) {
                if (data.features.length) {
                    standScenario2.addFeatures(app.geojson_format.read(data));
                    timemapScenarioData[opt2] = data;
                    processBreaks();
                    standScenario2.redraw();
                } else {
                    console.log("First scenario doesn't have any features! Check scenariostands...")
                    $("#error-timemap2").fadeIn();
                }
            });
        }
    }
};

function processBreaks() {

    var flatData = [];

    $.each( standScenario1.features, function(k,v) { 
        flatData.push(v.attributes.results[selectedTimeMapMetric]);
    });
    $.each( standScenario2.features, function(k,v) { 
        flatData.push(v.attributes.results[selectedTimeMapMetric]);
    });

    // flatten array of arrays into one big array
    flatData = [].concat.apply([], flatData);
    // Remove nulls
    flatData = flatData.filter(Number);

    var min = Math.min.apply(Math, flatData);
    var max = Math.max.apply(Math, flatData);

    // Equal interval classification
    var numclasses = 5;
    var range = max - min;
    var steprange = range/numclasses; 
    var steps = [];
    for (var i = 1; i < numclasses; i++) {
        steps.push((steprange*i) + min)
    };
    timemapBreaks = steps;
};

$(document).ready(function() {

    $("#scenario-maps-tab").on('shown', function() { refreshTimeMap(true, true); }); 
    $("#select-scenario1").change(function() { refreshTimeMap(true, false); }); 
    $("#select-scenario2").change(function() { refreshTimeMap(false, true); }); 

    var timemapInitialized = false;
    var context = {
        getColour: function(feature) {
            var color;

            var attr = feature.attributes.results[selectedTimeMapMetric][yearIndex]; 
            if (!attr) {
                return "#ccc";
            }
            var timemapColorRamp = ["#EDF8E9", "#BAE4B3", "#74C476", "#31A354", "#006D2C"];

            if (attr < timemapBreaks[0]) {
                color = timemapColorRamp[0];
            } else if (attr < timemapBreaks[1]) {
                color = timemapColorRamp[1];
            } else if (attr < timemapBreaks[2]) {
                color = timemapColorRamp[2];
            } else if (attr < timemapBreaks[3]) {
                color = timemapColorRamp[3];
            } else {
                color = timemapColorRamp[4];
            }

            return color;
        }
    };
    var template = {
        fillOpacity: 0.8,
        strokeColor: "#FFFFFF",
        strokeWidth: 1,
        fillColor: "${getColour}"
    };
    var style = new OpenLayers.Style(template, {context: context});
    var styleMap = new OpenLayers.StyleMap({'default': style});

    var apiKey = "AhYe6O-7ejQ1fsFbztwu7PScwp2b1U1vM47kArB_8P2bZ0jiyJua2ssOLrU4pH70";
    var aerial1 = new OpenLayers.Layer.Bing({
        name: "Bing Aerial",
        key: apiKey,
        type: "Aerial"
    });

    timemap1.addLayer(aerial1);
    standScenario1 = new OpenLayers.Layer.Vector("Scenario Stands",  {
        renderers: app.renderer, 
        styleMap: styleMap
    });
    timemap1.addLayer(standScenario1);

    var aerial2 = new OpenLayers.Layer.Bing({
        name: "Bing Aerial",
        key: apiKey,
        type: "Aerial"
    });
    timemap2.addLayer(aerial2);
    standScenario2 = new OpenLayers.Layer.Vector("Scenario Stands",  {
        renderers: app.renderer, 
        styleMap: styleMap
    });
    timemap2.addLayer(standScenario2);

    $("#timemap-backward").click(function(){
        var field = $('#field-year-slider');
        var val = parseInt(field.val());
        field.val(val - 5);  // assume 5 yr interval
        field.change();
    });
    $("#timemap-forward").click(function(){
        var field = $('#field-year-slider');
        var val = parseInt(field.val());
        field.val(val + 5);  // assume 5 yr interval
        field.change();
    });

    // Initialize sliders
    var field = $('#field-year-slider');
    var slidy = $('#slider-year-slider');
    var yearIndex = 0;

    onChange = function() {
        field.val(slidy.slider('value')); 
        var val = field.val();
        yearIndex = Math.floor((parseInt(val, 10) - 2013)/5);
        if (standScenario1) {
            standScenario1.redraw();
        }
        if (standScenario2) {
            standScenario2.redraw();
        }
    };
    slidy.slider({
        range: 'min',
        min : 2013, 
        max : 2108,
        step : 5,
        change : onChange,
        slide : onChange 
        //slide : function(event, ui) { field.val(slidy.slider('value')); }
    });
    slidy.slider("value", field.val() ); 
    field.change( function (){ 
        slidy.slider("value", field.val());
    }); 
});

