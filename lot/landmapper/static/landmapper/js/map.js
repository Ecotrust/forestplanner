var landmapper = {};

var mapView = new ol.View({
  center: ol.proj.fromLonLat([-122.41, 43.82]),
  zoom: 6.5
});

landmapper.selectedFeatureSource = new ol.source.Vector();

landmapper.selectedFeatureLayer = new ol.layer.Vector({
  source: landmapper.selectedFeatureSource
});

var map = new ol.Map({
  target: 'map',
  layers: [
    new ol.layer.Tile({
      source: new ol.source.OSM()
    }),
    landmapper.selectedFeatureLayer
  ],
  view: mapView
});

landmapper.showNextBtn = function(show) {
  if (show) {
    document.querySelector('#btn-content-panel-next').classList.remove('disabled');
  } else {
    document.querySelector('#btn-content-panel-next').classList.add('disabled');
  }
}

landmapper.loadTaxLots = function(mapEvent) {
  var lonlat = mapEvent.coordinate;
  let taxlotsURL = '/landmapper/get_taxlot_json/';

  jQuery.ajax({
    url: taxlotsURL,
    data: {
      'coords': lonlat
    },
    success: function(data) {
      var parsedData = JSON.parse(data);
      var wkt = parsedData['geometry'];
      var format = new ol.format.WKT();
      if (wkt == []) {
        window.alert('Taxlot info unavailable at this location - please draw instead.');
      } else {
        var feature = format.readFeature(wkt);
      }

      landmapper.selectedFeatureSource.addFeature(feature)
      // landmapper.selectedFeatureLayer.addFeatures([feature])
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
  landmapper.showNextBtn(true);
  landmapper.loadTaxLots(e);
});
