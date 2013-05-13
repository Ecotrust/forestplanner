app.scenarios.styleMap = new OpenLayers.StyleMap({
    "default": new OpenLayers.Style({
        fillColor: "${getColor}",
        fillOpacity: 0.8,
        strokeWidth: 1,
        strokeOpacity: 0.6

    }, {
        // Rules go here.
        context: {

            getColor: function(feature) {
                return feature.attributes.color ? feature.attributes.color : "#ccc";
            }
        }
    }),
    "select": {
        fillColor: "#8aeeef",
        strokeColor: "#32a8a9"
    }
});

function rxViewModel(options) {
    var self = this;

    self.myrx_id = options.myrx_id;
    self.rx_id = options.rx_id;
    self.name = ko.observable(options.name);
    self.description = ko.observable(options.description);
    self.color = options.color;
    self.editable = options.editable;
    self.rx_internal_name = options.rx_internal_name;
    self.confirmDelete = ko.observable(false);

    return self;
}

function scenarioFormViewModel(options) {
    var self = this;
    var colors = ['#ADD071', '#6AC247', '#339936', '#267373', '#349D7F', '#449FC1', '#6A86CD', 
                  '#7971D0', '#AB81D5', '#C79FDF', '#EBC6EC', '#D2A379', '#CCC266'];

    self.prescriptionList = ko.observableArray([]);
    self.inputRxs = ko.observable({});

    if (options && options.myrxList) {
        $.each(options.myrxList, function(i, myrx) {
            self.prescriptionList.unshift(new rxViewModel({
                name: myrx.name,
                description: myrx.description,
                myrx_id: myrx.myrx_id,
                rx_id: myrx.rx_id,
                rx_internal_name: myrx.rx_internal_name,
                color: colors.pop(),
                editable: true
            }));
        });
    }

    self.newRx = ko.observable(false);
    self.selectedRx = ko.observable();

    self.rxBeingEdited = null;

    // deciscion tree breadcrumbs:
    self.decisionOutput = ko.observableArray();

    self.updateRx = function() {
        var rx = this;
        self.rxBeingEdited = rx;
        self.selectedRx(new rxViewModel(ko.toJS(rx)));
    };

    self.deleteRx = function() {
        var rx = this;

        $.ajax({
            url: "/features/generic-links/links/delete/{uid+}/".replace('{uid+}', rx.myrx_id),
            type: "DELETE",
            success: function(result) {
                self.prescriptionList.remove(rx);
            }
        });
    };

    self.addNewRx = function() {
        self.newRx(true);
        decision(app.properties.viewModel.selectedProperty().variant_id(),

        // final callback for decision tree
        function(rx) {
            self.newRx(false);
            self.selectedRx(new rxViewModel({
                rx_internal_name: rx,
                color: colors.pop(),
                editable: true
            }));
        },
        // periodic updates for decision tree
        function(update) {
            if (update) {
                self.decisionOutput.push(update);    
            } else {
                self.decisionOutput.pop();
            }
        });
    };

    self.saveRx = function() {
        var url = '/features/myrx/form/',
            rx = self.selectedRx();

        if (rx.myrx_id) {
            url = "/features/myrx/{uid}/".replace('{uid}', rx.myrx_id);
        }

        $.ajax({
            url: url,
            type: 'POST',
            dataType: 'JSON',
            data: {
                rx_internal_name: self.selectedRx().rx_internal_name,
                name: self.selectedRx().name(),
                description: self.selectedRx().description()
            },
            success: function(result) {
                var rx_id = result["X-Madrona-Select"];

                if (rx.myrx_id) {
                    self.prescriptionList.replace(self.rxBeingEdited, self.selectedRx());
                    self.selectedRx(false);
                } else {
                    $.ajax({
                        url: _.string.sprintf('/features/forestproperty/%s/add/%s', app.properties.viewModel.selectedProperty().uid(), rx_id),
                        type: 'POST',
                        dataType: 'JSON',
                        data: {
                            rx_internal_name: self.selectedRx().rx_internal_name,
                            name: self.selectedRx().name(),
                            description: self.selectedRx().description()
                        },
                        success: function() {
                            self.prescriptionList.unshift(rx);
                            self.selectedRx(false);
                            self.decisionOutput([]);
                        }
                    });
                }
            }
        });
    };

    self.updateManagementStyle = function() {
        self.newRx(true);
        decision(app.properties.viewModel.selectedProperty().variant_id(), function(rx) {
            self.newRx(false);
            self.selectedRx().rx_internal_name = rx;
        });
    };

    self.cancel = function() {
        self.selectedRx(false);
        self.decisionOutput([]);

    };

    self.applyRx = function() {
        var myrx = this;

        $.each(app.stand_layer.selectedFeatures, function(i, feature) {
            feature.attributes.color = myrx.color;

            var stand_id = feature.data.uid.split("_")[2];
            var rx_id = myrx.rx_id;
            if (stand_id && rx_id) {
                self.inputRxs()[stand_id] = rx_id;
            } else {
                console.log("Can't add to inputRxs: stand_id and rx_id are ", feature.data, myrx)
            }
        });
        app.stand_layer.selectFeature.unselectAll();
    };


    self.selectedFeatures = ko.observable(false);

    // sometimes this happens too fast :()
    setTimeout(function() {
        app.stand_layer.selectFeature.onSelect = function(feature) {
            if (app.stand_layer.selectedFeatures.length > 0) {
                self.selectedFeatures(true);
            }
        };
        app.stand_layer.selectFeature.onUnselect = function(feature) {

            if (app.stand_layer.selectedFeatures.length === 0) {
                self.selectedFeatures(false);
            }
        };

    }, 900);


    return self;
}

function scenarioViewModel(options) {
    var self = this;

    self.showScenarioPanels = ko.observable(true);
    self.showScenarioList = ko.observable(false);
    self.scenarioList = ko.observableArray();
    self.selectedFeatures = ko.observableArray();
    self.activeScenario = ko.observable();

    self.scenarioForm = null;

    self.reloadScenarios = function(property) {
        // why is this here? 
        self.loadScenarios(property);
    };

    self.loadScenarios = function(property) {
        self.property = property;

        // update breadcrumbs
        app.breadCrumbs.breadcrumbs.removeAll();
        app.breadCrumbs.breadcrumbs.push({
            name: 'Properties',
            url: '/properties',
            action: self.cancelManageScenarios
        });
        app.breadCrumbs.breadcrumbs.push({
            url: 'scenarios/' + property.id(),
            name: property.name() + ' Scenarios',
            action: null
        });
        app.updateUrl();

        self.showScenarioList(true);
        self.toggleScenarioForm(false);

        map.zoomToExtent(property.bbox());
        var process = function(data) {
            self.scenarioList(data);
            if (data[0]) {
                self.selectedFeatures.push(data[0]); // select the first one
            }
            refreshCharts();
        };
        $.get('/features/forestproperty/links/property-scenarios/{property_id}/'.replace('{property_id}', property.uid()), process);
    };

    self.initialize = function(property) {
        // bind the viewmodel
        ko.applyBindings(self, document.getElementById('scenario-html'));
        ko.applyBindings(self, document.getElementById('scenario-outputs'));
        self.loadScenarios(property);
    };

    self.cancelManageScenarios = function() {
        app.breadCrumbs.breadcrumbs.pop();
        app.updateUrl();
        self.showScenarioPanels(false);
        app.properties.viewModel.showPropertyPanels(true);
        app.property_layer.setOpacity(1);
        if (app.stand_layer) app.stand_layer.removeAllFeatures();
        $('#scenario-form-metacontainer').hide();
        $('#searchbox-container').show();
        $('#map').fadeIn();
    };

    self.toggleFeature = function(f) {
        var removed = self.selectedFeatures.remove(f);
        if (removed.length === 0) { // add it
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
            success: function(data, textStatus, jqXHR) {
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
            $("#scenario-outputs").hide();
            $("#map").show();


            //$("div.outermap").hide();
        } else {
            $("div#scenario-form-metacontainer").hide();
            $("#scenario-outputs").show();
            $("#map").hide();
            if (app.stand_layer) {
                if (app.stand_layer.selectFeature) {
                    app.stand_layer.selectFeature.unselectAll();
                }
                app.stand_layer.removeAllFeatures();
                app.selectFeature.activate();
            }


            //$("div.outermap").show();
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

        $.get('/features/forestproperty/links/property-stands-geojson/{property_id}/'.replace('{property_id}', self.property.uid()), function(data) {

            if (app.stand_layer) {

                app.stand_layer.removeAllFeatures();
                app.stand_layer.selectFeature = new OpenLayers.Control.SelectFeature(app.stand_layer, {
                    "clickout": false,
                    "multiple": true,
                    "toggle": true
                });

            } else {

                app.stand_layer = new OpenLayers.Layer.Vector("Stands", {
                    styleMap: app.scenarios.styleMap,
                    renderers: app.renderer
                });

                map.addLayer(app.stand_layer);

                app.stand_layer.selectFeature = new OpenLayers.Control.SelectFeature(app.stand_layer, {
                    "clickout": false,
                    "multiple": true,
                    "toggle": true
                });
                app.scenarios.rubberBandActive = false;
                $(document).on('keyup keydown', function (e) {
                  if (e.shiftKey) {
                    
                    app.scenarios.rubberBandActive = true;
                    app.selectFeature.deactivate();
                    map.removeControl(app.selectFeature);
                    app.selectFeature = new OpenLayers.Control.SelectFeature(app.stand_layer,
                      { 
                        "clickout": false,
                        "multiple": true,
                        "toggle": true,
                        "box": true
                      }); 
                    map.addControl(app.selectFeature); 
                    app.selectFeature.activate();
                  } else {
                    if (app.scenarios.rubberBandActive) {
                    
                      app.scenarios.rubberBandActive = true;
                      app.selectFeature.deactivate();
                      map.removeControl(app.selectFeature);
                      app.selectFeature = new OpenLayers.Control.SelectFeature(app.stand_layer,
                      { 
                        "clickout": false,
                        "multiple": true,
                        "toggle": true,
                        "box": false
                      });
                      map.addControl(app.selectFeature); 
                      app.selectFeature.activate();
                    }
                  }
                });

                // reenable click and drag in vectors
                app.stand_layer.selectFeature.handlers.feature.stopDown = false;

                map.addControl(app.stand_layer.selectFeature);

            }

            app.stand_layer.addFeatures(app.geojson_format.read(data));

            // deactivate the property control
            app.selectFeature.deactivate();
            app.stand_layer.selectFeature.activate();

        });
        $.when(
        $.ajax({
            url: formUrl,
            type: "GET",
            success: function(data, textStatus, jqXHR) {
                $('#scenario-form-container').html(data);


                $('#scenario-form-container').find('button.cancel').click(function(e) {
                    e.preventDefault();
                    self.showScenarioList(true);
                    self.toggleScenarioForm(false);
                    $("form#scenario-form").empty();
                });
                $('#scenario-form-container').find('button.submit').click(function(e) {
                    e.preventDefault();
                    $("#id_input_property").val(app.properties.viewModel.selectedProperty().id());
                    $("#id_input_rxs").val(JSON.stringify(app.scenarios.formViewModel.inputRxs()));
                    var postData = $("form#scenario-form").serialize();
                    $.ajax({
                        url: postUrl,
                        type: "POST",
                        global: false, // prevent global ajaxError handler
                        data: postData,
                        dataType: "json",
                        success: function(data, textStatus, jqXHR) {
                            var uid = data["X-Madrona-Select"];
                            self.selectedFeatures.removeAll();
                            self.loadScenarios(self.property);
                            self.toggleScenarioForm(false);
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            if (jqXHR.status >= 400 && jqXHR.status < 500) {
                                // if there is a 4xx error
                                // assume madrona returns a form with error msgs 
                                data = $(jqXHR.responseText);
                                errors = data.find(".errorlist > *");
                                errorHtml = "";
                                $.each(errors, function(k,v) { 
                                    errorHtml += v.innerHTML + " . ";
                                });
                                app.flash(errorHtml, "Error saving scenario...");
                            }
                        }
                    });
                });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                alert(errorThrown);
            }
        }),
        $.ajax({
            url: '/features/forestproperty/links/property-myrx-json/' + app.properties.viewModel.selectedProperty().uid() + '/',
            type: "GET",
            dataType: "JSON",
            success: function(res) {
                app.scenarios.data = {
                    myrxList: res
                };
            }
        })).then(function() {
            app.scenarios.formViewModel = new scenarioFormViewModel(app.scenarios.data);
            ko.applyBindings(app.scenarios.formViewModel, document.getElementById('scenario-form-container'));
        });
    };

    return self;
}