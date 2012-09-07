function scenarioViewModel() {
  var self = this;

  self.showScenarioPanels = ko.observable(true);
  self.showScenarioList = ko.observable(false);
  self.showScenarioForm = ko.observable(false);
  self.scenarioList = ko.observableArray();
  self.selectedFeatures = ko.observableArray();

  self.reloadScenarios = function(property) {
    // why is this here? 
    self.loadScenarios(property);
  };

  self.loadScenarios = function(property) {
    self.property = property;
    console.log(property);
    
    // update breadcrumbs
    app.breadCrumbs.breadcrumbs.removeAll();
    app.breadCrumbs.breadcrumbs.push({url: '/', name: 'Home', action: null});
    app.breadCrumbs.breadcrumbs.push({name: 'Properties', url: '/properties', action: self.cancelManageScenarios});
    app.breadCrumbs.breadcrumbs.push({url: '/properties/scenarios', name: property.name() + ' Scenarios', action: null});

    self.showScenarioList(true);

    map.zoomToExtent(property.bbox());
    var process = function (data) {
        self.scenarioList(data);
        refreshCharts();
    };
    $.get('/features/forestproperty/links/property-scenarios/{property_id}/'.replace('{property_id}', property.uid()), process);
  }

  self.initialize = function(property) {
    // bind the viewmodel
    ko.applyBindings(self, document.getElementById('scenario-html'));
    self.loadScenarios(property);
  };

  self.cancelManageScenarios = function() {
    app.breadCrumbs.breadcrumbs.pop();
    self.showScenarioPanels(false);
    app.properties.viewModel.showPropertyPanels(true);
    app.property_layer.setOpacity(1);
  };

  self.toggleFeature = function(f) {
      var removed = self.selectedFeatures.remove(f);
      if (removed.length == 0) { // add it
        self.selectedFeatures.push(f);
      }
      refreshCharts();
  };

  self.addScenarioStart = function() {
    self.showScenarioList(false);
    self.showScenarioForm(true);
    formUrl = "/features/scenario/form/"; // TODO get from workspace
    $.ajax({
        url: formUrl,
        type: "GET",
        success: function(data, textStatus, jqXHR) {
            $('#scenario-form-container').html(data);
            $('form#scenario-form button.cancel').click( function(e) {
                e.preventDefault();
                self.showScenarioList(true);
                self.showScenarioForm(false);
                $("form#scenario-form").empty();
            });
            $('form#scenario-form button.submit').click( function(e) {
                e.preventDefault();
                var postData = $("form#scenario-form").serialize(); 
                $.ajax({
                    url: formUrl,
                    type: "POST",
                    data: postData,
                    dataType: "json",
                    success: function(data, textStatus, jqXHR) {
                        self.showScenarioList(true);
                        self.showScenarioForm(false);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        alert(errorThrown);
                    }
                });
            });
        },
        error: function(jqXHR, textStatus, errorThrown) {
            alert(errorThrown);
        }
    });
  };

  return self;
}
