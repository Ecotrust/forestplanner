window.addEventListener( 'load', function() {

  function generatePropertyReport(eFormSubmitted) {
    var propertyNameValue = document.getElementById('property-name').value;
    var taxlots = landmapper.taxlot_ids.split("&");
    if (taxlots.length >= 1) {
      landmapperReport.getReport(taxlots, propertyNameValue);
    }
  }

  const formGenerateReport = document.getElementById('form-property-name');
  formGenerateReport.addEventListener('submit', function(e) {
    e.preventDefault();
    generatePropertyReport(e);
  });

  formGenerateReport.addEventListener('keypress', function(e) {
    var keyCode = e.which;
    // console.log(keyCode);
    /*
      \ : 92 - gets interpreted as a literal by app server
      / : 47 - gets interpreted as a literal by app server
      | : 124 - is required for parsing lot ID from name
      ? : 63 - Gets interpreted as starting a query string? Breaks image requests, can be fixed
      # : 35 - gets interpreted as an anchor? Breaks image requests, can be fixed
    */
    var disallowed = [92, 47, 124, 63, 35];
    if (disallowed.indexOf(keyCode) >= 0) {
      $('#prop-name-error').css("visibility", "visible");
      e.preventDefault();
      return false;
    }
  })

});

var landmapperReport = {
  reportURL: '/landmapper/create_property_id/',
  getReport: function(taxlots, propertyName) {
    $('#spinner-modal').modal('show');
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
          $('#spinner-modal').modal('hide');
          window.alert('Error creating maps, please try again.');
          console.log('Error in craeting maps.');
      }
    });
  }
};
