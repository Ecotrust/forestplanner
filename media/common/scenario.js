function scenarioViewModel() {
  var self = this;

  self.showScenarioPanels = ko.observable(true);
  self.showScenarioHelp = ko.observable(false);
  self.showScenarioList = ko.observable(false);
  self.showDrawPanel = ko.observable(false);
  self.scenarioList = ko.observableArray();
  self.selectedFeature = ko.observable();

  self.reloadScenarios = function(property) {
    /*
    self.stand_layer.removeAllFeatures();
    self.standList.removeAll();
    self.property_layer.removeAllFeatures();
    map.addLayer(self.property_layer);
    map.addLayer(self.stand_layer);
    self.showScenarioList(true);
    app.selectFeature.deactivate();
    */
    self.loadScenarios(property);
      alert("reload scenarios");
  };

  self.loadScenarios = function(property) {
    self.property = property;
    
    // update breadcrumbs
    app.breadCrumbs.breadcrumbs.removeAll();
    app.breadCrumbs.breadcrumbs.push({url: '/', name: 'Home', action: null});
    app.breadCrumbs.breadcrumbs.push({name: 'Properties', url: '/properties', action: self.cancelManageScenarios});
    app.breadCrumbs.breadcrumbs.push({url: '/properties/scenarios', name: 'Scenarios', action: null});
    
    map.zoomToExtent(property.bbox());
    var process = function (data) {
        console.log(data);
    };
    console.log('getting scenarios');
    $.get('/features/forestproperty/links/property-scenarios-geojson/{property_id}/'.replace('{property_id}', property.uid()), process);
  }

  self.initialize = function(property) {
    // bind the viewmodel
    ko.applyBindings(self, document.getElementById('scenario-html'));
    self.loadScenarios(property);
    console.log("initialize");
  };

  self.cancelManageScenarios = function() {
    app.breadCrumbs.breadcrumbs.pop();
    self.showScenarioPanels(false);
      /*
    app.properties.viewModel.showPropertyPanels(true);
    app.property_layer.setOpacity(1);
    map.removeLayer(self.stand_layer);
    map.removeLayer(self.property_layer);
    app.drawFeature.featureAdded = app.properties.featureAdded;
    app.selectFeature.activate();
     */

  };

  self.addScenarioStart = function() {
    app.drawFeature.activate();
    self.showScenarioHelp(false);
    self.showScenarioList(false);
    self.showDrawPanel(true);
  };
  return self;
}
