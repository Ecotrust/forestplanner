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

standDrawn = function(e) {
  console.log('map drawn. ' + e);
  // show slide10 content
  // activate editing
  map.addInteraction(drawModify);
  map.addInteraction(drawSnap);
  // prepare to populate fields and submit form when user clicks finish button
}

clearDrawing = function() {
  drawSource.clear();
}

startDrawing = function() {
  map.removeInteraction(drawModify);
  map.removeInteraction(drawSnap);
  map.addInteraction(drawInteraction);
}

stopDrawing = function() {
  map.removeInteraction(drawInteraction);
}
