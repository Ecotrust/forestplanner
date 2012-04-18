
function standsViewModel() {
  var self = this;

  // display the form panel entirely
  self.showStandPanels = ko.observable();
  // display initial help
  self.showStandHelp = ko.observable(true);
  // display drawing help
  self.showDrawPanel = ko.observable(false);
  // display form
  self.showStandFormPanel = ko.observable(false);
  // display list of stands
  self.showStandList = ko.observable(true);

  self.showNoStandHelp = ko.observable(true);

  self.standList = ko.observableArray();

  self.selectedFeature = ko.observable();

  self.cancelManageStands = function() {
    self.showStandPanels(false);
    app.properties.viewModel.showPropertyPanels(true);
    app.property_layer.setOpacity(1);
    map.removeLayer(self.stand_layer);
    map.removeLayer(self.property_layer);
    app.drawFeature.featureAdded = app.properties.featureAdded;
    app.selectFeature.activate();
  }

  self.addStandStart = function() {
    app.drawFeature.activate();
    self.showStandHelp(false);
    self.showStandList(false);
    self.showDrawPanel(true);
  }

  self.showStandForm = function(action, uid) {
    // get the form
    var formUrl;
    if (action === "create") {
      formUrl = app.workspace["feature-classes"][0]["link-relations"]["create"]["uri-template"]; 
    } else if (action === "edit") {
      formUrl = app.workspace["feature-classes"][0]["link-relations"]["edit"][0]["uri-template"]; 
      formUrl = formUrl.replace('{uid}', uid);
    }
    // clean up and show the form
    $.get(formUrl, function(data) {
      var $form = $(data).find('form');
      $form.find('input:submit').remove();
      // app.cleanupForm($form);
      $('#stands-form-container').empty().append($form);
      self.showNoStandHelp(false);
      self.showStandFormPanel(true);
      $form.find('input:visible:first').focus();
      $form.bind('submit', function(event) {
        event.preventDefault();
      });
    })
   
  }

  self.updateStand = function(stand_id, isNew) {
    var updateUrl = '/features/generic-links/links/geojson/{uid}/'.replace('{uid}', stand_id);
    $.get(updateUrl, function(data) {
      if (isNew) {
        self.stand_layer.addFeatures(app.geojson_format.read(data));
      } else {
        debugger;
        ko.mapping.fromJS(data.features[0].properties, self.selectedFeature());
        self.showStandFormPanel(false);
        self.showStandList(true);
      }
    });
  }

  self.associateStand = function(stand_id, property_id) {
    var url = "/features/forestproperty/{forestproperty_uid}/add/{stand_uid}";
    url = url.replace('{forestproperty_uid}', property_id).replace('{stand_uid}', stand_id);
    $.ajax({
      url: url,
      type: "POST",
      success: function(data) {
        self.updateStand(JSON.parse(data)["X-Madrona-Select"], true);
        app.stands.viewModel.showStandFormPanel(false);
        app.stands.viewModel.showStandList(true);
        app.new_features.removeAllFeatures();
      }
    })

  }

  self.saveStandForm = function(self, event) {
    var isNew, $dialog = $('#stands-form-container'),
      $form = $dialog.find('form'),
      actionUrl = $form.attr('action'),
      values = {},
      error = false;
    $form.find('input,select').each(function() {
      var $input = $(this);
      if ($input.closest('.field').hasClass('required') && $input.attr('type') !== 'hidden' && !$input.val()) {
        error = true;
        $input.closest('.control-group').addClass('error');
        $input.siblings('p.help-block').text('This field is required.');
      } else {
        values[$input.attr('name')] = $input.val();
      }
    });
    if (error) {
      return false;
    }
    if (self.modifyFeature.active) {
      values.geometry_final = values.geometry_orig = self.modifyFeature.feature.geometry.toString();
      self.modifyFeature.deactivate();
      isNew = false;
    } else {
      values.geometry_final = values.geometry_orig = app.stands.geometry;
      isNew = true;
    }
    $form.addClass('form-horizontal');
    $.ajax({
      url: actionUrl,
      type: "POST",
      data: values,
      success: function(data, textStatus, jqXHR) {
        var stand_uid = JSON.parse(data)["X-Madrona-Select"];
        // property is not defined if new
        if (isNew) {
          self.associateStand(stand_uid, self.property.uid());
        } else {
          self.updateStand(stand_uid, false);
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        self.cancelAddStand();
      }
    });
  };

  // start the stand editing process
  self.editStand = function() {
    self.modifyFeature.selectFeature(self.selectedFeature().feature);
    self.modifyFeature.activate();
    self.showStandList(false);
    self.showStandForm("edit", self.selectedFeature().uid());
  };

  self.cancelAddStand = function () {
    self.showStandFormPanel(false);
    self.showStandHelp(true);
    self.showStandList(true);
    self.showDrawPanel(false);
    app.new_features.removeAllFeatures();
    app.drawFeature.deactivate();
    if (self.modifyFeature.active) {
      self.modifyFeature.resetVertices();
      self.modifyFeature.deactivate();
    }
    self.showNoStandHelp(true);
  }

  self.selectFeature = function(feature, event) {
    self.selectedFeature(feature);
  }

  self.initialize = function(property) {
    // bind the viewmodel
    ko.applyBindings(self, document.getElementById('stand-html'));

    // start the stand manager
    self.property_layer = new OpenLayers.Layer.Vector("Active Property", {
      renderers: app.renderer,
      styleMap: new OpenLayers.StyleMap({
        fillOpacity: 0,
        strokeWidth: 2,
        strokeOpacity: 1,
        strokeColor: "#44ff00"
      })
    });
    map.addLayer(self.property_layer);

    //map.zoomToExtent(self.property_layer.getDataExtent());
    app.stands.featureAdded = function(feature) {
      app.drawFeature.deactivate();
      self.showDrawPanel(false);
      app.stands.geometry = feature.geometry.toString();
      self.showStandForm("create");
      //app.saveFeature(feature);
    };

    self.stand_layer = new OpenLayers.Layer.Vector("Stands", {
      styleMap: app.new_styles,
      renderers: app.renderer
    });
    
    map.addLayer(self.stand_layer);
    self.modifyFeature = new OpenLayers.Control.ModifyFeature(self.stand_layer);
    map.addControl(self.modifyFeature);

    self.stand_layer.events.on({
      'featureselected': function(feature) {},
      'featureadded': function(feature) {
        var featureViewModel = ko.mapping.fromJS(feature.feature.data);
        // save a reference to the feature
        featureViewModel.feature = feature.feature;
        // add it to the viewmodel
        self.standList.unshift(featureViewModel);
      },
      'featuresadded': function(data) {}
    });
    map.addLayer(self.stand_layer);

    self.snapper = new OpenLayers.Control.Snapping({
      layer: app.new_features,
      targets: [self.property_layer, self.stand_layer],
      greedy: false
    });
    self.snapper.activate();
    self.loadStands(property);
  }

  self.reloadStands = function(property) {
    self.stand_layer.removeAllFeatures();
    self.standList.removeAll();
    self.property_layer.removeAllFeatures();
    map.addLayer(self.property_layer);
    map.addLayer(self.stand_layer);
    self.loadStands(property);
    self.showStandList(true);
  }

  self.loadStands = function(property) {
    self.property = property;
    app.drawFeature.featureAdded = app.stands.featureAdded;
    app.selectFeature.deactivate();
    self.property_layer.addFeatures(property.feature.clone());
    // TODO get this url from workspace doc
    $.get('/features/forestproperty/links/property-stands-geojson/{property_id}/'.replace('{property_id}', property.uid()), function(data) {
      if (data.features.length) {
        self.stand_layer.addFeatures(app.geojson_format.read(data));
        self.showStandHelp(false);
      } else {
        self.showStandHelp(true);
      }
    });

  }

  return self;
}
