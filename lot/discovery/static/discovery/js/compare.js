scenarios = {};
for (var i = 0; i < scenario_list.length; i++) {
  scenario = scenario_list[i];
  scenarios[scenario.pk] = scenario.fields;
}

$('input:checkbox').on('change', function(e) {
  id = parseInt(e.currentTarget.value);
  if (e.currentTarget.checked) {
    console.log('Scenario ' + id + ' checked!');
    // Add scenario's data to metrics
  } else {
    console.log('Scenario ' + id + ' unchecked!');
    // Remove scenario's data from metrics
    // If this can't be done, then you'll have to re-run metrics without it :(
  }

});

// Create D3 graphs for each metric

// add listeners to checkboxes to toggle adding/removing data from graphs by ID
