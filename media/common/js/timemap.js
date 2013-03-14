var timemap1 = new OpenLayers.Map();
var timemap2 = new OpenLayers.Map();
var standScenario1;
var standScenario2;

$(document).ready(function() {

    $("#scenario-maps-tab").on('shown', function (e) {
        //e.target // activated tab
        //e.relatedTarget // previous tab
        if (!timemapInitialized) {
            timemap1.render("timemap1");
            timemap2.render("timemap2");
            timemap1.zoomToExtent(OpenLayers.Bounds.fromArray([-13954802.50397, 5681411.4375898, -13527672.389972, 5939462.8450446]));
            timemap2.zoomToExtent(OpenLayers.Bounds.fromArray([-13954802.50397, 5681411.4375898, -13527672.389972, 5939462.8450446]));
            var c1, c2, z1, z2;
            var updatingMap1 = false;
            var updatingMap2 = false;
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

            // TODO AGGGGG this is hideous !!! hook to app.scenario.viewModel 
            // or better yet make this whole function part of the viewmodel and bindings
            var f1 = app.scenarios.viewModel.scenarioList()[0];
            var geojson_url = "/features/generic-links/links/geojson/trees_scenario_" + f1.pk +"/";
            $.get( geojson_url, function(data) {
                if (data.features.length) {
                    standScenario1.addFeatures(app.geojson_format.read(data));        
                    var bounds = standScenario1.getDataExtent();
                    if (bounds) { 
                        timemap1.zoomToExtent(bounds);
                    }
                } 
            });
            var f2 = app.scenarios.viewModel.scenarioList()[1];
            var geojson_url2 = "/features/generic-links/links/geojson/trees_scenario_" + f2.pk +"/";
            $.get( geojson_url2, function(data) {
                if (data.features.length) {
                    standScenario2.addFeatures(app.geojson_format.read(data));        
                    var bounds = standScenario2.getDataExtent();
                    if (bounds) { 
                        timemap2.zoomToExtent(bounds);
                    }
                } 
            });

            timemapInitialized = true;
        }
    });

    var timemapInitialized = false;
    var context = {
        getColour: function(feature) {
            var color;
            var attr = feature.attributes.results.carbon[yearIndex]; 
            // TODO assumes 0-20 range
            if (attr < 4) {
                color = "#EDF8E9";
            } else if (attr < 8) {
                color = "#BAE4B3";
            } else if (attr < 12) {
                color = "#74C476";
            } else if (attr < 16) {
                color = "#31A354";
            } else {
                color = "#006D2C";
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
    //timemap1.addControl(new OpenLayers.Control.LayerSwitcher());
    standScenario1 = new OpenLayers.Layer.Vector("Properties",  {
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
    standScenario2 = new OpenLayers.Layer.Vector("Properties",  {
        renderers: app.renderer, 
        styleMap: styleMap
    });
    timemap2.addLayer(standScenario2);

});

var field = $('#field-year-slider');
var slidy = $('#slider-year-slider');
var yearIndex = 0;

onChange = function() {
    field.val(slidy.slider('value')); 
    var val = field.val();
    yearIndex = Math.floor((parseInt(val, 10) - 2020)/20);
    if (standScenario1) {
        standScenario1.redraw();
    }
    if (standScenario2) {
        standScenario2.redraw();
    }
};
slidy.slider({
    range: 'min',
    min : 2020, 
    max : 2120,
    step : 20,
    change : onChange,
    slide : onChange 
    //slide : function(event, ui) { field.val(slidy.slider('value')); }
});
slidy.slider("value", field.val() ); 
field.change( function (){ 
    slidy.slider("value", field.val());
}); 
