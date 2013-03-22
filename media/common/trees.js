
var map, controls;
var stands;
var currentStep = 1;
var steps = [undefined]; // start with a blank to make it 1-indexed

function init() {
    map = new OpenLayers.Map(); 

    var bingApiKey = "AhYe6O-7ejQ1fsFbztwu7PScwp2b1U1vM47kArB_8P2bZ0jiyJua2ssOLrU4pH70";
    var hybrid = new OpenLayers.Layer.Bing({
        name: "Bing Hybrid",
        key: bingApiKey,
        type: "AerialWithLabels"
    });
    map.addLayer(hybrid);

    // for (var i=map.layers.length-1; i>=0; --i) {
    //      map.layers[i].animationEnabled = true;
    // }

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

