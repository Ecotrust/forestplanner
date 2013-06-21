
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

  // pagination config will display x items 
  // from this zero based index
  self.listStart = ko.observable(0);
  self.listDisplayCount = 25;

  // list of all stands, primary viewmodel
  self.standList = ko.observableArray();

  // paginated list
  self.standListPaginated = ko.computed(function () {
    return self.standList.slice(self.listStart(), self.listDisplayCount+self.listStart());
  });

  // this list is model for pagination controls 
  self.paginationList = ko.computed(function () {
    var list = [], displayIndex = 1, listIndex = 0;
    
    for (listIndex=0; listIndex < self.standList().length; listIndex++) {
      if (listIndex % self.listDisplayCount === 0 && Math.abs(listIndex - self.listStart()) < 5 * self.listDisplayCount) {
        list.push({'displayIndex': 1 + (listIndex/self.listDisplayCount), 'listIndex': listIndex });
      }
    }
    /*
    if (list.length < self.standList().length / self.listDisplayCount) {
        list.push({'displayIndex': '...', 'listIndex': null });
        list.push({'displayIndex': '»', 'listIndex': null });
    }
    if (self.listStart() > 10) {
        list.shift({'displayIndex': '&laquo;', 'listIndex': null });      
    }
    //console.log('repaginating list');
    */
    return list;
  });

  self.setListIndex = function (button, event) {
    var listStart = self.listStart();
    if (button.displayIndex === '»') {
      self.listStart(listStart + self.listDisplayCount * 5);
    } else {
    self.listStart(button.listIndex);
    }
    //console.log(self.listStart());
    self.selectFeature(self.standList()[button.listIndex || self.listStart()]);
  };

  // this will get bound to the active stand
  self.selectedFeature = ko.observable();

  // progress bar config
  self.progressBarWidth = ko.observable("0%");
  self.showProgressBar = ko.observable(false);

  self.cancelManageStands = function() {
    app.breadCrumbs.breadcrumbs.pop();
    //app.updateUrl();
    self.showStandPanels(false);
    app.properties.viewModel.showPropertyPanels(true);
	
    //these are breaking tab switching. seems to be working without them!
    //uh oh?
    //map.removeLayer(self.stand_layer);
    //map.removeLayer(self.property_layer);
    app.drawFeature.featureAdded = app.properties.featureAdded;
    app.selectFeature.activate();
  };

  self.refineBoundaries = function() {
    $("#refine-boundaries-dialog").modal("show");
  };

  self.refineVegetation = function() {
    $("#refine-vegetation-dialog").modal("show");
  };

  self.addStandStart = function() {
    app.drawFeature.activate();
    self.showStandHelp(false);
    self.showStandList(false);
    self.showDrawPanel(true);
  };

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
    });
  };

  self.updateStand = function(stand_id, isNew) {
    var updateUrl = '/features/generic-links/links/geojson/{uid}/'.replace('{uid}', stand_id);
    $.get(updateUrl, function(data) {
      if (isNew) {
        self.stand_layer.addFeatures(app.geojson_format.read(data));
        self.standList.unshift(ko.mapping.fromJS(data.features[0].properties));
        self.selectedFeature(self.standList()[0]);
      } else {
        ko.mapping.fromJS(data.features[0].properties, self.selectedFeature());
        self.showStandFormPanel(false);
        self.showStandList(true);
      }
    });
  };

  self.associateStand = function(stand_id, property_id) {
    var url = "/features/forestproperty/{forestproperty_uid}/add/{stand_uid}";
    url = url.replace('{forestproperty_uid}', property_id).replace('{stand_uid}', stand_id);
    $.ajax({
      url: url,
      type: "POST",
      success: function(data) {
        self.updateStand(JSON.parse(data)["X-Madrona-Select"], true);
        app.stands.viewModel.showStandFormPanel(false);
        //app.stands.viewModel.showStandList(true);
        app.new_features.removeAllFeatures();
      }
    });
  };

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
      //values.geometry_final = values.geometry_orig = app.stands.geometry;
      values.geometry_orig = app.stands.geometry;
      isNew = true;
    }
    $form.addClass('form-horizontal');
    $.ajax({
      url: actionUrl,
      type: "POST",
      data: values,
      success: function(data, textStatus, jqXHR) {
        var stand_uid = JSON.parse(data)["X-Madrona-Select"];
        if (isNew) {
          self.associateStand(stand_uid, self.property.uid());
          self.addStandStart();  // automatically go back to digitizing mode
        } else {
          self.updateStand(stand_uid, false);
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        self.cancelAddStand();
      }
    });
  };

  self.showDeleteDialog = function () {
    $("#stand-delete-dialog").modal("show");
  };

  self.deleteFeature = function () {
    var url = "/features/generic-links/links/delete/{uid}/".replace("{uid}", self.selectedFeature().uid());
    $('#stand-delete-dialog').modal('hide');
    $.ajax({
      url: url,
      type: "DELETE",
      success: function (data, textStatus, jqXHR) {
        self.stand_layer.removeFeatures(self.stand_layer.getFeaturesByAttribute("uid", self.selectedFeature().uid()));
        self.standList.remove(self.selectedFeature());
      }  
    });
  };

  // start the stand editing process
  self.editStand = function() {
    self.modifyFeature.selectFeature(self.stand_layer.selectedFeatures[0]);
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
  };

  self.selectFeature = function(feature, event) {
    self.selectControl.unselectAll();
    self.selectControl.select(self.stand_layer.getFeaturesByAttribute("uid", feature.uid())[0]);
    self.selectedFeature(feature);
  };

  self.initialize = function(property) {
    // bind the viewmodel
    ko.applyBindings(self, document.getElementById('stand-html'));

    // start the stand manager
    self.property_layer = new OpenLayers.Layer.Vector("My Active Property", {
      renderers: app.renderer,
      styleMap: map_styles.standProperty
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
      styleMap: map_styles.stand,
      renderers: app.renderer
    });

    app.stand_layer = self.stand_layer;

    //
    //  Snapping controls for drawing/editing stands
    //
    new_snap = new OpenLayers.Control.Snapping({
                layer: app.new_features,
                targets: [app.property_layer, app.stand_layer],
                greedy: false
            });
    new_snap.activate();
    var stand_snap = new OpenLayers.Control.Snapping({
            layer: self.stand_layer,
            targets: [app.property_layer, app.stand_layer],
            greedy: false
        });
    stand_snap.activate();

    map.addLayer(self.stand_layer);
    self.modifyFeature = new OpenLayers.Control.ModifyFeature(self.stand_layer);
    map.addControl(self.modifyFeature);

    self.stand_layer.events.on({
      'featureselected': function(feature) {
        // use true as second argument to indicate map event
        self.selectFeatureById(feature.feature.data.uid);
      },
      'featureadded': function(feature) {
        // var featureViewModel = ko.mapping.fromJS(feature.feature.data);
        // console.log('loading ' + feature.feature.data.name);
        // // save a reference to the feature in the viewmodel
        // featureViewModel.feature = feature.feature;
        // // add it to the viewmodel
        // self.standList.unshift(featureViewModel);
      },
      'featuresadded': function(data) {}
    });
    map.addLayer(self.stand_layer);

    self.selectControl = new OpenLayers.Control.SelectFeature(self.stand_layer,
        { "clickout": false});

    self.selectControl.onBeforeSelect = function (feature) {
     // debugger;
    };
    
    // reenable click and drag in vectors
    self.selectControl.handlers.feature.stopDown = false; 
    map.addControl(self.selectControl);
    self.selectControl.activate();

    self.loadStands(property);
  };

  self.selectFeatureById = function (id) {
    var pageSize = self.standList().length / self.listDisplayCount;
    $.each(self.standList(), function (i, feature) {
      if (feature.uid() === id) {
        // set list start to first in list page      
        self.listStart(Math.floor(i / self.listDisplayCount) * self.listDisplayCount);
        self.selectedFeature(this);
      }
    });
  };

  self.loadViewModel = function (data) {
    var percent = 90;
    self.standList($.map(data.features, function (feature, i) {
        var remaining = 10 * i/data.length;
        self.progressBarWidth(percent + remaining + "%");
        return ko.mapping.fromJS(feature.properties);
    }));
    self.selectFeature(self.standList()[0]);
  };

  self.reloadStands = function(property) {
    self.stand_layer.removeAllFeatures();
    self.standList.removeAll();
    self.property_layer.removeAllFeatures();
    map.addLayer(self.property_layer);
    map.addLayer(self.stand_layer);
    self.loadStands(property);
    self.showStandList(true);
    app.selectFeature.deactivate();
    self.progressBarWidth("0%");
    self.showProgressBar(true);
  };

  self.loadStands = function(property) {
    var i = 0,
      timer = setInterval(function () {
        self.progressBarWidth(i*15+"%");
        i++;
        if (i > 90) { clearInterval(timer);}
    }, 100);
    self.showNoStandHelp(false);
    self.property = property;
	console.info('stands.loadStands self.property = property', property);

    app.drawFeature.featureAdded = app.stands.featureAdded;
    self.property_layer.addFeatures(property.feature.clone());
    
    // update breadcrumbs
    app.breadCrumbs.breadcrumbs.removeAll();
    app.breadCrumbs.breadcrumbs.push({name: 'Properties', url: '/properties', action: self.cancelManageStands});
    app.breadCrumbs.breadcrumbs.push({url: 'stands/' + property.id(), name: property.name() + ' Stands', action: null});
    //app.updateUrl();
    
    map.zoomToExtent(property.bbox());
    // TODO get this url from workspace doc
    var key = 'stand_' +  property.uid();
    var process = function (data) {
      if (data.features.length) {
        self.stand_layer.addFeatures(app.geojson_format.read(data));
        self.loadViewModel(data);
      } else {
        self.showStandHelp(true);
        self.showNoStandHelp(true);

      }
      self.showProgressBar(false);
      self.progressBarWidth("0%");

    };

    self.showProgressBar(true);
    //console.log('getting stands');
    $.get('/features/forestproperty/links/property-stands-geojson/{property_id}/'.replace('{property_id}', property.uid()), process);
  };

  return self;
}
