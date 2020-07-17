var mapView = new ol.View({
  center: ol.proj.fromLonLat([-122.41, 43.82]),
  zoom: 6.5
});

var map = new ol.Map({
  target: 'map',
  layers: [
    new ol.layer.Tile({
      source: new ol.source.OSM()
    })
  ],
  view: mapView
});

var showNextBtn = function(show) {
  if (show) {
    document.querySelector('#btn-content-panel-next').classList.remove('disabled');
  } else {
    document.querySelector('#btn-content-panel-next').classList.add('disabled');
  }
}

var loadTaxLots = function(mapEvent) {
  // var lonlat = map.coordinate;
  var lonlat = ol.proj.toLonLat(mapEvent.coordinate)
  // print(e)
  let taxlotsURL = '/landmapper/get_taxlot_json';

  jQuery.ajax({
    url: taxlotsURL,
    data: {
      'coords': [lonlat[0], lonlat[1]]
    },
    success: function(data) {
        // var format = new OpenLayers.Format.WKT();
        // wkt = data.geometry;
        if (wkt == []) {
          window.alert('Taxlot info unavailable at this location - please draw instead.');
        } else {
          // feature = format.read(wkt);
          // if (! feature) {
            // For some reason, we get GeoJSON back instead of WKT
            // Clearly a bug in Madrona, but for now, just go with it.
            // format = new OpenLayers.Format.GeoJSON();
            // feature = format.read(wkt)[0];
            console.log(data);
          // }
        }
        //Add feature to vector layer
        // app.viewModel.scenarios.drawingFormModel.polygonLayer.addFeatures([feature]);
        // app.viewModel.scenarios.drawingFormModel.consolidatePolygonLayerFeatures();
        // app.viewModel.scenarios.drawingFormModel.hasShape(true);
    },
    error: function(error) {
        window.alert('Error retrieving taxlot - please draw instead.');
        console.log('error in map.js: Click Control trigger');
    }
  });
};


map.on('click', function(e) {
  showNextBtn(true);
  loadTaxLots(e);
});
