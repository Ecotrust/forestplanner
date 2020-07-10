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
