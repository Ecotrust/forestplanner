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
        options[options.length] = new Option(text, parseInt(val));
    });
  });
});
