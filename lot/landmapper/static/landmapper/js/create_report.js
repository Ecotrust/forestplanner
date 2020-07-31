window.addEventListener( 'load', function() {

  function generatePropertyReport(eFormSubmitted) {
    var propertyNameValue = document.getElementById('property-name').value;
    var parts = landmapper.getLocationHashParts();
    if (parts.length === 5) {
      taxlots = parts[4].split('&');
      landmapperReport.getReport(taxlots, propertyNameValue);
    }
  }

  const formGenerateReport = document.getElementById('form-property-name');
  formGenerateReport.addEventListener('submit', function(e) {
    e.preventDefault();
    generatePropertyReport(e);
  });
});

var landmapperReport = {
  reportURL: '/landmapper/create_property_id/',
  getReport: function(taxlots, propertyName) {
    var token = document.querySelector('[name=csrfmiddlewaretoken]').value;
    jQuery.ajax({
      headers: { "X-CSRFToken": token },
      url: landmapperReport.reportURL,
      method: 'POST',
      data: {
        'taxlot_ids': taxlots,
        'property_name': propertyName
      },
      success: function(data) {
        var parsedData = JSON.parse(data);
        console.log(parsedData)
        var propertyId = parsedData['property_id'];
        var origin = window.location.origin;
        return window.location.href = `${origin}/landmapper/report/${propertyId}`;

        // var wkt = parsedData['geometry'];
        // var lot_id = parsedData['id'];
        // var format = new ol.format.WKT();
        // if (wkt == []) {
        //   window.alert('Taxlot info unavailable at this location - please draw instead.');
        // } else {
        //   var feature = format.readFeature(wkt);
        // }
        // landmapper.selectedFeatureSource.addFeature(feature);
        // if (landmapper.taxlot_ids.length > 0) {
        //   landmapper.taxlot_ids = landmapper.taxlot_ids + '&' + lot_id;
        // } else {
        //   landmapper.taxlot_ids = landmapper.taxlot_ids + lot_id;
        // }

        // when have property redirect to report
          // redirect to /report/${property_id}

      },
      error: function(error) {
          window.alert('Error creating maps, please try again.');
          console.log('Error in craeting maps.');
      }
    });
  }
};
