function scenarioViewModel() {
  var self = this;

  self.showScenarioPanels = ko.observable(true);
  self.showScenarioList = ko.observable(false);
  self.scenarioList = ko.observableArray();
  self.selectedFeatures = ko.observableArray();
  self.activeScenario = ko.observable();

  self.reloadScenarios = function(property) {
    // why is this here? 
    self.loadScenarios(property);
  };

  self.loadScenarios = function(property) {
    self.property = property;
    
    // update breadcrumbs
    app.breadCrumbs.breadcrumbs.removeAll();
    app.breadCrumbs.breadcrumbs.push({url: '/', name: 'Home', action: null});
    app.breadCrumbs.breadcrumbs.push({name: 'Properties', url: '/properties', action: self.cancelManageScenarios});
    app.breadCrumbs.breadcrumbs.push({url: '/properties/scenarios', name: property.name() + ' Scenarios', action: null});

    self.showScenarioList(true);
    self.toggleScenarioForm(false);

    map.zoomToExtent(property.bbox());
    var process = function (data) {
        self.scenarioList(data);
        if (data[0]) {
            self.selectedFeatures.push(data[0]); // select the first one
        }
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
    $('#scenario-outputs').hide();
    $('#searchbox-container').show();
    $('#map').fadeIn();
  };

  self.toggleFeature = function(f) {
      var removed = self.selectedFeatures.remove(f);
      if (removed.length == 0) { // add it
        self.selectedFeatures.push(f);
      }
      refreshCharts();
  };

  self.showDeleteDialog = function(f) {
      self.activeScenario(f);
      $("#scenario-delete-dialog").modal("show");
  };

  self.deleteFeature = function() {
    var url = "/features/generic-links/links/delete/trees_scenario_{pk}/".replace("{pk}", self.activeScenario().pk);
    $.ajax({
        url: url,
        type: "DELETE",
        success: function (data, textStatus, jqXHR) {
            self.selectedFeatures.remove(self.activeScenario());
            self.scenarioList.remove(self.activeScenario());
            refreshCharts();
        },  
        complete: function() {
            self.activeScenario(null);
            $("#scenario-delete-dialog").modal("hide");
        }
    });
  };

  self.editFeature = function(f) {
      self.activeScenario(f);
      self.addScenarioStart(true);
  };

  self.newScenarioStart = function() {
      self.activeScenario(null);
      self.addScenarioStart(false);
  };

  self.toggleScenarioForm = function(stat) {
      // self.showScenarioForm(stat);
      if (stat) {
          $("div#scenario-form-metacontainer").show();
          $("div.outermap").hide();
      } else {
          $("div#scenario-form-metacontainer").hide();
          $("div.outermap").show();
      }
  };

  self.addScenarioStart = function(edit_mode) {
    self.showScenarioList(false);
    self.toggleScenarioForm(true);
    // TODO get formUrl from workspace
    if (self.activeScenario() && edit_mode) {
        formUrl = "/features/scenario/trees_scenario_{pk}/form/".replace('{pk}', self.activeScenario().pk);
        postUrl = formUrl.replace("/form", "");
    } else {
        formUrl = "/features/scenario/form/"; 
        postUrl = formUrl;
    }
    $.ajax({
        url: formUrl,
        type: "GET",
        success: function(data, textStatus, jqXHR) {
            $('#scenario-form-container').html(data);
            $('#scenario-form-container').find('button.cancel').click( function(e) {
                e.preventDefault();
                self.showScenarioList(true);
                self.toggleScenarioForm(false);
                $("form#scenario-form").empty();
            });
            $('#scenario-form-container').find('button.submit').click( function(e) {
                e.preventDefault();
                $("#id_input_property").val(app.properties.viewModel.selectedProperty().id());
                var postData = $("form#scenario-form").serialize(); 
                $.ajax({
                    url: postUrl,
                    type: "POST",
                    data: postData,
                    dataType: "json",
                    success: function(data, textStatus, jqXHR) {
                        var uid = data["X-Madrona-Select"];
                        self.selectedFeatures.removeAll();
                        self.loadScenarios(self.property); 
                        self.toggleScenarioForm(false);
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
