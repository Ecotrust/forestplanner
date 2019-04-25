$(document).ready(function() {
  // function loadStratumEntryTable() {
  //   var createStratumBtn = document.querySelector('button[data-bind="click: createStratum"]');
  //   console.log(createStratumBtn);
  //   if (createStratumBtn) {
  //     createStratumBtn.click();
  //     window.clearTimeout();
  //   } else {
  //     window.setTimeout(function() {
  //       loadStratumEntryTable();
  //     }, 1000);
  //   }
  // }

  // not sure why jquery says dom is ready but click() won't work without settimeout below
  // best guess is the knockout observables are not ready yet
  // TODO: Find a better way than settimeout
  // window.setTimeout(function() {
  //   loadStratumEntryTable();
  // }, 1000);
  $('.field-species select').on('change', function(e) {
    var species = e.currentTarget.value;
    var row_id = e.currentTarget.id.split('-')[1];
    var size_class_selector = $('#id_form-'+ row_id + '-size_class');
    var size_select_values = {};
    if (species.length > 0) {
      var size_classes = choice_json.filter(function(o){return o.species == species;} )[0].size_classes;

      for (var i=0; i < size_classes.length; i++) {
        size_select_values["("+ size_classes[i].min + ", " + size_classes[i].max + ")"] = size_classes[i].min + '" to ' + size_classes[i].max + '"';
      }
    }
    if(size_class_selector.prop) {
      var options = size_class_selector.prop('options');
    } else {
      var options = size_class_selector.attr('options');
    }
    $('option', size_class_selector).remove();
    $.each(size_select_values, function(val, text) {
        options[options.length] = new Option(text, val);
    });
  });

});

total_forms = parseInt($('#id_form-TOTAL_FORMS').val());
initial_forms = parseInt($('#id_form-INITIAL_FORMS').val());
init_show = initial_forms > 2 ? initial_forms + 1 : 3;
form_show_index = init_show;
for (var i = 0; i < init_show; i++) {
  $('#formset-row-' + i).show();
}

submitForm = function() {
  $.ajax({
    type: "POST",
    url: $('#stand_strata_form').attr('action'),
    data: $('#stand_strata_form').serialize(),
    success: function(data){
      window.location = "/discovery/forest_profile/" + discovery_stand_uid + "/"
    }
  });
}

addRow = function() {
  if (form_show_index < total_forms) {
    $('#formset-row-' + form_show_index).show();
    form_show_index++;
  } else {
    alert('Cannot add more rows at this time. Please save and return to this form to add more.');
  }
}
