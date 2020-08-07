/**
 * [landmapper description]
 * @type {Object}
 * Encapsulation of app related objects
 * defaults for center zoom rotation
 */
var landmapper = {
  zoom: 7,
  center: [-13429137.91,5464036.81],
  rotation: 0,
  taxlot_ids: '',
  getLocationHashParts: function() {
    var hash = window.location.hash.replace('#map=', '');
    var parts = hash.split('/');
    return parts;
  }
};


/**
 * [Permalink checker]
 * @method if
 * @param  {[type]} window [description]
 * @return {[type]}        [description]
 * Check if permalink in URL
 */
if (window.location.hash !== '') {
  // try to restore center, zoom-level, rotation, and taxlots from the URL
  var parts = landmapper.getLocationHashParts();
  if (parts.length === 5) {
    landmapper.zoom = parseInt(parts[0], 10);
    landmapper.center = [
      parseFloat(parts[1]),
      parseFloat(parts[2])
    ];
    landmapper.rotation = parseFloat(parts[3]);
    landmapper.taxlot_ids = parts[4]
  }
}


/**
 * [mapView description]
 * @type {ol}
 */
var mapView = new ol.View({
  center: landmapper.center,
  zoom: landmapper.zoom,
  rotation: landmapper.rotation
});


/**
 * [selectedFeatureSource description]
 * @type {ol}
 */
landmapper.selectedFeatureSource = new ol.source.Vector();

landmapper.selectedFeatureStyles = new ol.style.Style({
  fill: new ol.style.Fill({
    color: 'rgba(255, 231, 49, 0.25)',
  }),
  stroke: new ol.style.Stroke({
    color: '#FFE731',
    width: 2,
  }),
});

landmapper.selectedFeatureLayer = new ol.layer.Vector({
  source: landmapper.selectedFeatureSource,
  style: landmapper.selectedFeatureStyles,
});


/**
 * [map description]
 * @type {ol}
 */
var map = new ol.Map({
  target: 'map',
  layers: [
    new ol.layer.Tile({
      visible: true,
      title: 'Aerial With Labels',
      preload: Infinity,
      source: new ol.source.BingMaps({
        imagerySet: 'AerialWithLabels',
        key: 'Ave7UcBYYPahWffLRpKbOAIo22WuwCpLuvUauhw_h6U4FOFMXZNCDnl3O3OTgxdF'
      })
    }),
    landmapper.selectedFeatureLayer
  ],
  view: mapView
});

/**
 * [description]
 * @method
 * @param  {[type]} show [description]
 * @return {[type]}      [description]
 */
landmapper.showNextBtn = function(show) {
  var btnNext = document.getElementById('btn-content-panel-next');
  var formPropertyName = document.getElementById('form-property-name');
  if (show) {
    btnNext.classList.remove('disabled');
    btnNext.addEventListener('click', function(e) {
      formPropertyName.classList.remove('d-none');
      e.preventDefault();
    })
  } else {
    btnNext.classList.add('disabled');
    formPropertyName.classList.add('d-none');
  }
}

/**
 * [description]
 * @method
 * @param  {[type]} mapEvent [description]
 * @return {[type]}          [description]
 */
landmapper.loadTaxLots = function(mapEvent) {
  var selectFeature = true;
  var pixel = map.getEventPixel(mapEvent.originalEvent);
  var pixelCoords = map.getCoordinateFromPixel(pixel);
  // Check if taxlot is already selected
  var featuresAtPixel = landmapper.selectedFeatureSource.getFeaturesAtCoordinate(pixelCoords);
  // var feature = featuresAtPixel.length ? featuresAtPixel[0] : undefined;
  console.log(featuresAtPixel);
  if (featuresAtPixel.length > 0) {
    selectFeature = false;
    landmapper.selectedFeatureSource.removeFeature(featuresAtPixel[0]);
  }
  var lonlat = mapEvent.coordinate;
  var taxlotsURL = '/landmapper/get_taxlot_json/';

  if (selectFeature) {
    jQuery.ajax({
      url: taxlotsURL,
      data: {
        'coords': lonlat
      },
      success: function(data) {
        var parsedData = JSON.parse(data);
        var wkt = parsedData['geometry'];
        var lot_id = parsedData['id'];
        var format = new ol.format.WKT();
        if (wkt == []) {
          window.alert('Taxlot info unavailable at this location - please draw instead.');
        } else {
          var feature = format.readFeature(wkt);
        }
        landmapper.selectedFeatureSource.addFeature(feature);
        if (landmapper.taxlot_ids.length > 0) {
          landmapper.taxlot_ids = landmapper.taxlot_ids + '&' + lot_id;
        } else {
          landmapper.taxlot_ids = landmapper.taxlot_ids + lot_id;
        }
      },
      error: function(error) {
          window.alert('Error retrieving taxlot - please draw instead.');
          console.log('error in map.js: Click Control trigger');
      }
    }).done(function() {
      updatePermalink();
    });
  }
};


/**
 * Track state in browser URL
 * @type {Boolean}
 */
var shouldUpdate = true;


/**
 * Update browser URL with Map state
 * @method
 * @return {[type]} [description]
 */
var updatePermalink = function() {
  if (!shouldUpdate) {
    // do not update the URL when the view was changed in the 'popstate' handler
    shouldUpdate = true;
    return;
  }

  landmapper.center = mapView.getCenter();
  landmapper.hash = '#map=' +
      mapView.getZoom() + '/' +
      landmapper.center[0] + '/' +
      landmapper.center[1] + '/' +
      mapView.getRotation() + '/' +
      landmapper.taxlot_ids;
  landmapper.state = {
    zoom: mapView.getZoom(),
    center: mapView.getCenter(),
    rotation: mapView.getRotation(),
    taxlot_ids: landmapper.taxlot_ids
  };
  window.history.pushState(landmapper.state, 'map', landmapper.hash);
};


/**
 * Map events
 * @method
 * @param  {[type]} e [description]
 * @return {[type]}   [description]
 */
map.on('singleclick', function(e) {
  landmapper.showNextBtn(true);
  landmapper.loadTaxLots(e);
});


/**
 * Update permalink
 * @type {[type]}
 */
map.on('moveend', updatePermalink);


// restore the view state when navigating through the history, see
// https://developer.mozilla.org/en-US/docs/Web/API/WindowEventHandlers/onpopstate
window.addEventListener('popstate', function(event) {
  if (event.state === null) {
    return;
  }
  mapView.setCenter(event.state.center);
  mapView.setZoom(event.state.zoom);
  mapView.setRotation(event.state.rotation);
  // TODO: style the taxlots
  shouldUpdate = false;
});
