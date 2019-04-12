$('.grid-card').on('click', function(e) {
  var uid = e.currentTarget.getAttribute('cardId');
  var url = e.currentTarget.getAttribute('modalsource');
  $.ajax({
    url: url,
    success: function(html) {
      $('#grid-modal-body').html(html);
    },
    error: function(error) {
      var html = "<h3>Error retrieving Data</h3><p>" + error + "</p>";
      $('#grid-modal-body').html(html);
    }
  })
})
