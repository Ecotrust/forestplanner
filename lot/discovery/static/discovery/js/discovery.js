$(document).ready(function() {
  $('#stand-modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var propertyName = button.data('property'); // Extract info from data-* attributes
    var propertyImg = button.data('img');
    // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
    var modal = $(this);
    modal.find('.modal-title').text('Property Name: ' + propertyName);
    modal.find('.modal-image').attr('src', propertyImg);
  });
});
