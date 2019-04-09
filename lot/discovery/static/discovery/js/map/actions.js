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
