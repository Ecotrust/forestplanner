

function standsViewModel () {
    var self = this;

    // display the form panel entirely
    self.showStandPanels = ko.observable();
    // display initial help
    self.showStandHelp = ko.observable(true);
    // display drawing help
    self.showDrawPanel = ko.observable(false);
    // display form
    self.showStandForm = ko.observable(false);
    // display list of stands
    self.showStandList = ko.observable(true);

    self.showNoStandHelp = ko.observable(true);

    self.standList = ko.observableArray();

    self.cancelManageStands = function () {
        self.showStandPanels(false);
        app.properties.viewModel.showPropertyPanels(true);
        app.property_layer.setOpacity(1);
        map.removeLayer(self.stand_layer);
        map.removeLayer(self.property_layer);
        app.drawFeature.featureAdded = app.properties.featureAdded;
        app.selectFeature.activate();
    }

    self.addStandStart = function () {
        app.drawFeature.activate();
        self.showStandHelp(false);
        self.showStandList(false);
        self.showDrawPanel(true);
    }
    
    self.addStandForm = function () {
        // get the form
        var formUrl = app.workspace["feature-classes"][0]["link-relations"]["create"]["uri-template"];
        // clean up and show the form
        $.get(formUrl, function (data) {
          var $form = $(data).find('form');
          $form.find('input:submit').remove();
          // app.cleanupForm($form);
          $('#stands-form-container').empty().append($form);
          self.showNoStandHelp(false);
          self.showStandForm(true);
          $form.find('input:visible:first').focus();
          $form.bind('submit', function (event) {
            event.preventDefault();
            //self.addFeature(self, event);
          });
        })
        // activate drawing
        // on save submit form and geometry
        // get the new feature and add it to observable array
    }

    self.updateStand = function (stand_id) {
      var updateUrl = '/features/generic-links/links/geojson/{uid}/'.replace('{uid}',stand_id);
      $.get(updateUrl, function (data) {
        self.stand_layer.addFeatures(app.geojson_format.read(data));
      });
    }

    self.associateStand = function (stand_id, property_id) {
        var url = "/features/forestproperty/{forestproperty_uid}/add/{stand_uid}";
        url = url.replace('{forestproperty_uid}', property_id);
        url = url.replace('{stand_uid}', stand_id);
        $.ajax({
            url: url,
            type: "POST",
            success: function (data) {
              self.updateStand(JSON.parse(data)["X-Madrona-Select"]);
              app.stands.viewModel.showStandForm(false);
              app.stands.viewModel.showStandList(true);
              app.new_features.removeAllFeatures();
            }
        })
       
    }

    self.saveStandForm = function (self, event) {
      var $dialog = $('#stands-form-container'),
        $form = $dialog.find('form'), 
        actionUrl = $form.attr('action'),
        values = {}, error=false;
      $form.find('input,select').each(function () {
        var $input = $(this);
        if ($input.closest('.field').hasClass('required') && $input.attr('type') !== 'hidden' && ! $input.val()) {
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
      values.geometry_final = values.geometry_orig = app.stands.geometry;
      $form.addClass('form-horizontal');
      $.ajax({
        url: actionUrl,
        type: "POST",
        data: values,
        success: function (data, textStatus, jqXHR) {
          // property is not defined if new
          self.associateStand(JSON.parse(data)["X-Madrona-Select"], self.property.uid());
        },
        error: function (jqXHR, textStatus, errorThrown) {
          self.cancelAddStand();
        }
      });
    };

    self.cancelAddStand = function () {
      self.showStandForm(false);
      self.showStandHelp(true);
      self.showStandList(true);
      self.showDrawPanel(false);
      app.new_features.removeAllFeatures()
      app.drawFeature.deactivate();
      self.showNoStandHelp(true);
    }



    self.initialize = function (property) {
      // bind the viewmodel
      ko.applyBindings(self, document.getElementById('stand-html'));

      // start the stand manager
      self.property_layer = new OpenLayers.Layer.Vector("Active Property",  {
                      renderers: app.renderer, 
                      styleMap: new OpenLayers.StyleMap({
                              fillOpacity: 0,
                              strokeWidth: 2,
                              strokeOpacity: 1,
                              strokeColor: "#44ff00",
                          })
                  });
      map.addLayer(self.property_layer);
      //map.zoomToExtent(self.property_layer.getDataExtent());
      app.stands.featureAdded = function(feature) { 
        app.drawFeature.deactivate();
        self.showDrawPanel(false);
        app.stands.geometry = feature.geometry.toString();
        self.addStandForm();
        //app.saveFeature(feature);
      };

      self.stand_layer = new OpenLayers.Layer.Vector("Stands",  {
                      renderers: app.renderer, 
                      styleMap:  new OpenLayers.StyleMap({
                          fillOpacity: .3,
                          fillColor: "brown",
                          strokeWidth: 1,
                          strokeOpacity: 1,
                          strokeColor: "brown",
                      })
                  });
      map.addLayer(self.stand_layer);
      self.stand_layer.events.on({
        'featureselected': function (feature) {
        },
        'featureadded': function (feature) {
          var featureViewModel = ko.mapping.fromJS(feature.feature.data);
          // save a reference to the feature
          featureViewModel.feature = feature.feature;
          // add it to the viewmodel
          self.standList.unshift(featureViewModel);
        },
        'featuresadded': function (data) {
        }
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

    self.reloadStands = function (property) {
      self.stand_layer.removeAllFeatures();
      self.standList.removeAll();
      self.property_layer.removeAllFeatures();
      map.addLayer(self.property_layer);
      map.addLayer(self.stand_layer);  
      self.loadStands(property);
      self.showStandList(true);
    }

    self.loadStands = function (property) {
      self.property = property;
      app.drawFeature.featureAdded = app.stands.featureAdded;
      app.selectFeature.deactivate();
      self.property_layer.addFeatures(property.feature.clone());
      $.get('/trees/property_stand_list/{property_id}/'.replace('{property_id}', property.uid()), function (data) {
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

