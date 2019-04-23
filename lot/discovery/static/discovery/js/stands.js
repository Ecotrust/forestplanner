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

deleteRUS = function(action) {
  var option = confirm("Are you sure you want to delete this stand permanently?");
  if (option) {
    $.ajax({
      url: action,
      method: 'DELETE',
      success: function(data) {
        location.reload();
      },
      error: function(data) {
        alert('Could not delete. (' + data.status + ') ' + data.statusText + ': ' + data.responseText);
      }
    });
  }
};
