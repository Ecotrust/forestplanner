var madrona = {
    onShow: function (callback) {
        callback();
        //madrona.formCallbacks.push(callback);
    },
    formCallbacks: [],
    features: {}
};

var app = {
    stands: {},
    scenarios: {},
    properties: {}
};

if (page_context(user.is_authenticated){
  $.get('/features/{{user.username}}/workspace-owner.json', function (data) {
    app.workspace = data;
  });
} else {
  $.get('/features/workspace-public.json', function (data) {
    app.workspace = data;
  });
}

// to go into scenarios.js
app.scenarios = {
    property_id: "{{ property_id }}",
    prescriptions: []
};


//</script>

//<script>

app.scenarios.init = function () {

  app.scenarios.viewModel = new scenarioViewModel2();
  ko.applyBindings(app.scenarios.viewModel, document.getElementById('scenarios-html'));





  app.selectFeature = new OpenLayers.Control.SelectFeature(app.stand_layer,
      {
          "clickout": false,
          "multiple": true,
          "toggle": true
      });

  // reenable click and drag in vectors
  app.selectFeature.handlers.feature.stopDown = false;

  map.addControl(app.selectFeature);
  app.selectFeature.activate();
};

function scenarioViewModel2 () {
  var self = this;

  self.scenarioList = ko.mapping.fromJS(app.scenarios.data);
  return self;
}

$.when(
    $.get('/features/forestproperty/links/property-scenarios/{property_id}/'.replace('{property_id}', app.scenarios.property_id), function (data) {
      app.scenarios.data = data;
    }),
    $.get('/features/generic-links/links/geojson/{uid}/'.replace('{uid}', app.scenarios.property_id), function (data) {
        map.render('map');
        map.updateSize();
        app.property_layer.addFeatures(app.geojson_format.read(data));
        map.zoomToExtent(app.property_layer.getDataExtent());

    }),
    $.get('/features/forestproperty/links/property-stands-geojson/{property_id}/'.replace('{property_id}', app.scenarios.property_id), function (data) {
        app.stand_layer = new OpenLayers.Layer.Vector("Stands", {
          styleMap: map_styles.stand,
          renderers: app.renderer
        });

        app.stand_layer.styleMap.default = new OpenLayers.Style({
          fillColor: "blue",


        }, {
          // Rules go here.
          context: {

          }
        });

        map.addLayer(app.stand_layer);
        app.stand_layer.addFeatures(app.geojson_format.read(data));
    })
).then(function () {

    app.scenarios.init();
});
