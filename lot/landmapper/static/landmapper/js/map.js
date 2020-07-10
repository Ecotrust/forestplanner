var mapView = new ol.View({
  center: ol.proj.fromLonLat([-122.41, 37.82]),
  zoom: 4
});

var map = new ol.Map({
  target: 'map',
  layers: [
    new ol.layer.Tile({
      // preload: Infinity,
      title: 'Satellite Imagery',
      source: new ol.source.XYZ({
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attributions: 'Sources: Esri, DigitalGlobe, Earthstar Geographics, CNES/Airbus DS, GeoEye, USDA FSA, USGS, Getmapping, Aerogrid, IGN, IGP, and the GIS User Community'
      }),
      name: 'Satellite',
      type: 'base',
      visible: false
    }),
  ],
  view: mapView
});
