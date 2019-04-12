$('#search-place-form').submit(function(e){
  e.preventDefault();
  var searchTerm = $('#search-place-input').val();
  $.ajax({
    url:"/trees/geosearch/?search=" + searchTerm,
    success: function(data) {
      map.getView().fit(data.extent);
      var currentZoom = map.getView().getZoom();
      if (currentZoom > 15) {
        map.getView().setZoom(15);
      }
    },
    error: function(data) {
      alert("Search '" + data.responseJSON.search + "' " + data.responseJSON.status + ": " + data.statusText);
    }
  });
});

updateStandGeomField = function() {
  var standGeom = drawSource.getFeatures()[0].getGeometry();
  var wktFormat = new ol.format.WKT();
  $('#id_geometry_final').val(wktFormat.writeGeometry(standGeom));
  $('#stand-form').change();
}

standDrawn = function(e) {
  // show slide10 content
  $('.pre-draw').hide();
  $('.post-draw').show();
  // activate editing
  map.addInteraction(drawModify);
  map.addInteraction(drawSnap);
  // prepare to populate fields and submit form when user clicks finish button
  setTimeout(function() {updateStandGeomField();}, 50);
}

loadDrawn = function() {
  var wktFormat = new ol.format.WKT();
  var feature = wktFormat.readFeature($('#id_geometry_final').val(), {
    dataProjection: 'EPSG:3857',
    featureProjection: 'EPSG:3857'
  });
  drawSource.addFeature(feature);
  standDrawn(null);
  map.getView().fit(drawSource.getFeatures()[0].getGeometry().getExtent());
}

standModified = function(e) {
  setTimeout(function() {updateStandGeomField();}, 50);
}

clearDrawing = function() {
  drawSource.clear();
}

startDrawing = function() {
  map.removeInteraction(drawModify);
  map.removeInteraction(drawSnap);
  $('.post-draw').hide();
  $('.pre-draw').show();
  map.addInteraction(drawInteraction);
}

stopDrawing = function() {
  map.removeInteraction(drawInteraction);
}

restartDrawing = function() {
  clearDrawing();
  $("#id_name").val(null);
  $("#id_geometry_final").val(null);
  startDrawing();
}
