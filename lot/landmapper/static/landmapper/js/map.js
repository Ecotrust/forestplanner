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
 * [mapView description]
 * @type {ol}
 */
var mapView = new ol.View({
  center: landmapper.center,
  zoom: landmapper.zoom,
  rotation: landmapper.rotation
});

landmapper.taxlotLayer = new ol.layer.Tile({
  visible: true,
  title: 'Taxlots',
  source: new ol.source.XYZ({
    url: 'https://api.mapbox.com/styles/v1/forestplanner/ckdgho51i084u1inx1a70iwim/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoiZm9yZXN0cGxhbm5lciIsImEiOiJja2J2MDg4MW8wMWNhMnRvYXkzc3I4czRxIn0.1TONAGYOeYpgrZZKivD-2g',
    attributions: "TBD"
  })
});

/**
 * [selectedFeatureSource description]
 * @type {ol}
 */
landmapper.selectedFeatureSource = new ol.source.Vector();

landmapper.selectedFeatureSource.on("addfeature", function(e){
  landmapper.showNextBtn(true);
});

landmapper.selectedFeatureSource.on("removefeature", function(e){
  if (landmapper.selectedFeatureSource.getFeatures().length < 1) {
    landmapper.showNextBtn(false);
  }
});

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
  title: 'Selected Taxlots',
  source: landmapper.selectedFeatureSource,
  style: landmapper.selectedFeatureStyles,
});

landmapper.pushPinOverlay = new ol.Overlay({
  position: ol.proj.fromLonLat([0,0]),
  // positioning: 'bottom-center',
  element: document.getElementById('pushPin'),
  stopEvent: false,
  offset: [-30, -50]
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
    })
  ],
  view: mapView
});

landmapper.bufferExtent = function(source_extent) {
    [west, south, east, north] = source_extent;
    width = east-west;
    width_buffer = width/10;
    height = north-south;
    height_buffer = height/10;
    buffered_extent = [west-width_buffer, south-height_buffer, east+width_buffer, north+height_buffer];
    return buffered_extent;
}

landmapper.showPropertyNameForm = function(e) {
    var formPropertyName = document.getElementById('form-property-name');
    formPropertyName.classList.remove('d-none');
    e.preventDefault();
    extent = landmapper.bufferExtent(landmapper.selectedFeatureSource.getExtent());
    mapView.fit(extent, {'duration': 1000});
}

landmapper.backToIdentify = function() {
    var formPropertyName = document.getElementById('form-property-name');
    formPropertyName.classList.add('d-none');
}

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
    //prevent duplicate events
    btnNext.removeEventListener('click', landmapper.showPropertyNameForm);
    btnNext.addEventListener('click', landmapper.showPropertyNameForm);
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
  // bool true if selecitng an unselected taxlot. Checked and changed later
  var selectFeature = true;
  var pixel = map.getEventPixel(mapEvent.originalEvent);
  var pixelCoords = map.getCoordinateFromPixel(pixel);

  // Check if taxlot is already selected
  var featuresAtPixel = landmapper.selectedFeatureSource.getFeaturesAtCoordinate(pixelCoords);
  if (featuresAtPixel.length > 0) {
    selectFeature = false;
    landmapper.selectedFeatureSource.removeFeature(featuresAtPixel[0]);
  }
  var lonlat = mapEvent.coordinate;
  var taxlotsURL = '/landmapper/get_taxlot_json/';

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
      // Select feature is bool if true add taxlot
      if (selectFeature) {
        if (wkt == []) {
          window.alert('Taxlot info unavailable at this location. This be due to an application error, please retry. If you recieve this message again, it may be because this data has not been made available by the county.');
        } else {
          var feature = format.readFeature(wkt);
        }
        landmapper.selectedFeatureSource.addFeature(feature);
        if (landmapper.taxlot_ids.length > 0) {
          landmapper.taxlot_ids = landmapper.taxlot_ids + '&' + lot_id;
        } else {
          landmapper.taxlot_ids = landmapper.taxlot_ids + lot_id;
        }
      } else {
        // If selectFeature is false remove taxlot
        var startAmpersand = landmapper.taxlot_ids.includes('&' + lot_id);
        var endAmpersand = landmapper.taxlot_ids.includes(lot_id + '&');
        if (startAmpersand) {
          landmapper.taxlot_ids = landmapper.taxlot_ids.replace('&' + lot_id, '');
        } else if (endAmpersand) {
          landmapper.taxlot_ids = landmapper.taxlot_ids.replace(lot_id + '&', '');
        } else {
          landmapper.taxlot_ids = landmapper.taxlot_ids.replace(lot_id, '');
        }
      }

    },
    error: function(error) {
        window.alert('Error: No taxlot data found');
        console.log('error in map.js: Click Control trigger');
    }
  });
};


/**
 * Track state in browser URL
 * @type {Boolean}
 */
var shouldUpdate = true;

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

map.selectNewGeocode = function(coords) {
  reprojectCoords = ol.proj.fromLonLat([coords[1],coords[0]])
  setWGS84Center(reprojectCoords);
  setPinCoords(reprojectCoords);

}

// set map location
var setWGS84Center = function(coords) {
  mapView.setCenter(reprojectCoords);
}

var setPinCoords = function(coords) {
  landmapper.pushPinOverlay.setPosition(coords);
}

var enableGeocodeResultSelection = function(coords, geocode_count) {
  map.addOverlay(landmapper.pushPinOverlay);
  reprojectCoords = ol.proj.fromLonLat(coords);
  setPinCoords(reprojectCoords);
  if (geocode_count > 1) {
    $("#content-panel-content").hide();
  } else{
    enablePropertySelection();
  }
  $('#pushPin').show();
}

var enablePropertySelection = function() {
  $("#geocode-results-options").hide();
  $("#content-panel-content").show();
  map.addLayer(landmapper.taxlotLayer);
  map.addLayer(landmapper.selectedFeatureLayer);
  /**
   * Map events
   * @method
   * @param  {[type]} e [description]
   * @return {[type]}   [description]
   */
  map.on('singleclick', function(e) {
    landmapper.loadTaxLots(e);
  });
}

var geocodeResultIssue = function(coords, geocode_count) {
  let error_message = "Unknown error occurred. Please double-check your input and if you continue to get an error, feel free to reach out to landmapper@ecotrust.org for assistance.";
  if (geocode_count == 0) {
    error_message = "No properties matching your search were found. Please note that this tool is designed only for properties in the state of Oregon. If your property is in Oregon, please try another search term or use the map to find it.";
  }

  mapView.setZoom(landmapper.zoom);

  $("#error-modal div#error-modal-content").html(error_message);
  $("#error-modal").modal('show');
}
