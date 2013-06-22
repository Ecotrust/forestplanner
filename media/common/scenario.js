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
    var colors = ['#A6CEE3', '#1F78B4', '#B2DF8A', '#33A02C', '#8DD3C7', '#E31A1C', '#FDBF6F', 
                  '#FF7F00', '#CAB2D6', '#6A3D9A', '#FFFF99', '#FB9A99', '#FFFFB3',
                  '#BEBADA', '#FB8072', '#80B1D3', '#FDB462', '#B3DE69', '#FCCDE5',
                  '#D9D9D9', '#BC80BD', '#CCEBC5', '#AAAAAA', '#777777', '#000000'];

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
                color: colors[i],
                editable: true
            }));
        });
    }

    self.newRx = ko.observable(false);
    self.selectedRx = ko.observable();

    self.rxBeingEdited = null;

    // decision tree breadcrumbs:
    self.decisionOutput = ko.observableArray();

    self.nWithRx = ko.observable(0);
    self.total = app.rx_stand_layer.features.length;
    self.remainder = function () {
        return self.total - self.nWithRx();
    };

    self.updateWithRx = function() {
         var with_rx = 0; 
         $.each(self.inputRxs(), function(k,f) { 
            with_rx++; 
         }); 
         self.nWithRx(with_rx++);
    };

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
            }
        );
    };

    self.saveRx = function() {
        var url = '/features/myrx/form/',
            rx = self.selectedRx();

        if (rx.myrx_id) {
            url = "/features/myrx/{uid}/".replace('{uid}', rx.myrx_id);
        }

        var desc = self.selectedRx().description();
        if (!desc) {
            self.selectedRx().description(self.decisionOutput().join(", \n"));
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
                var rx_uid = result["X-Madrona-Select"];

                if (rx.myrx_id) {
                    self.prescriptionList.replace(self.rxBeingEdited, self.selectedRx());
                    self.selectedRx(false);
                } else {
                    $.ajax({
                        url: _.string.sprintf('/features/forestproperty/%s/add/%s', app.properties.viewModel.selectedProperty().uid(), rx_uid),
                        type: 'POST',
                        dataType: 'JSON',
                        // data: {
                        //     rx_internal_name: self.selectedRx().rx_internal_name,
                        //     name: self.selectedRx().name(),
                        //     description: self.selectedRx().description()
                        // },
                        success: function() {
                            self.prescriptionList.unshift(rx);
                            self.selectedRx(false);
                            self.decisionOutput([]);
                        }
                    });
                }

                // reload the entire list of myrxs
                $.ajax({
                    url: '/features/forestproperty/links/property-myrx-json/' + app.properties.viewModel.selectedProperty().uid() + '/',
                    type: "GET",
                    dataType: "JSON",
                    success: function(res) {
                        if (res) {
                            self.prescriptionList.removeAll();
                            $.each(res, function(i, myrx) {
                                self.prescriptionList.unshift(new rxViewModel({
                                    name: myrx.name,
                                    description: myrx.description,
                                    myrx_id: myrx.myrx_id,
                                    rx_id: myrx.rx_id,
                                    rx_internal_name: myrx.rx_internal_name,
                                    color: colors[i],
                                    editable: true
                                }));
                            });
                        }
                    }
                });
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

        $.each(app.rx_stand_layer.selectedFeatures, function(i, feature) {
            feature.attributes.color = myrx.color;

            var stand_id = feature.data.uid.split("_")[2];
            var rx_id = myrx.rx_id;
            if (stand_id && rx_id) {
                self.inputRxs()[stand_id] = rx_id;
            } else {
                console.log("Can't add to inputRxs: stand_id and rx_id are ", feature.data, myrx)
            }
        });
        app.rx_stand_layer.selectFeature.unselectAll();
        self.updateWithRx();
    };

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

    self.reloadScenarios = function() {
        property = app.properties.viewModel.selectedProperty();
        self.property = property;
        self.loadScenarios(property);
        self.scenarioList.removeAll();
        self.selectedFeatures.removeAll();
        self.showScenarioList(true);
        self.showScenarioPanels(true);
        timemapScenarioData = {};
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
        //app.updateUrl();

        self.showScenarioList(true);
        self.toggleScenarioForm(false);

        map.zoomToExtent(property.bbox());
        var process = function(data) {
            self.scenarioList(data);
            if (data[0]) {
                self.selectedFeatures.push(data[0]); // select the first one
            }
            refreshCharts();
            refreshTimeMap(true, true);
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
        //app.breadCrumbs.breadcrumbs.pop();
        //app.updateUrl();
        self.showScenarioPanels(false);
		self.toggleScenarioForm('hide')
        //app.properties.viewModel.showPropertyPanels(true);
        if (app.rx_stand_layer)
            app.rx_stand_layer.removeAllFeatures();
        $('#scenario-form-metacontainer').hide();
        $('#searchbox-container').show();
        $('#map').fadeIn();
        timemapInitialized = false; 
    };

    self.toggleFeature = function(f) {
        var removed = self.selectedFeatures.remove(f);
        if (removed.length === 0) { // add it
            self.selectedFeatures.push(f);
        }
        refreshCharts();
        //refreshTimeMap();
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
        $('#scenario-form-container').html("<h4>Loading...</h4>"); 
        self.activeScenario(null);
        self.addScenarioStart(false);
    };


    self.toggleScenarioForm = function(stat) {
        // self.showScenarioForm(stat);
        if (stat) {
            $("div#scenario-form-metacontainer").show();
            $("#scenario-outputs").hide();
            $("#map").show();
        } else {
            $("div#scenario-form-metacontainer").hide();
            $("#scenario-outputs").show();
            $("#map").hide();
            if (app.rx_stand_layer) {
                if (app.rx_stand_layer.selectFeature) {
                    app.rx_stand_layer.selectFeature.unselectAll();
                }
                app.rx_stand_layer.removeAllFeatures();
                app.selectFeature.activate();
            }
        }
    };


    self.addScenarioStart = function(edit_mode) {
        self.showScenarioList(false);
        self.toggleScenarioForm(true);

        if (self.activeScenario() && edit_mode) {
            formUrl = "/features/scenario/trees_scenario_{pk}/form/".replace('{pk}', self.activeScenario().pk);
            postUrl = formUrl.replace("/form", "");
        } else {
            formUrl = "/features/scenario/form/";
            postUrl = formUrl;
        }

        // Fire off 3 Async calls
        $.when(
            // #1 - load the stands geojson
            $.get('/features/forestproperty/links/property-stands-geojson/{property_id}/'.replace('{property_id}', self.property.uid()), 

                function(data) {
                    if (app.rx_stand_layer) {
                        app.rx_stand_layer.removeAllFeatures();
                    } else {

                        app.rx_stand_layer = new OpenLayers.Layer.Vector("Stands", {
                            styleMap: map_styles.scenarios,
                            renderers: app.renderer
                        });

                        map.addLayer(app.rx_stand_layer);

                        app.rx_stand_layer.selectFeature = new OpenLayers.Control.SelectFeature(app.rx_stand_layer, {
                            "clickout": false,
                            "multiple": true,
                            "toggle": true
                        });

                        app.rx_stand_layer.selectFeatureBox = new OpenLayers.Control.SelectFeature(app.rx_stand_layer, {
                            "clickout": false,
                            "multiple": true,
                            "toggle": true,
                            "box": true
                        });

                        app.scenarios.rubberBandActive = false;
                        $(document).on('keyup', function (e) {
                            if (app.scenarios.rubberBandActive) {
                                app.scenarios.rubberBandActive = false;
                                app.rx_stand_layer.selectFeatureBox.deactivate();
                                app.rx_stand_layer.selectFeature.activate();
                            }
                        });

                        $(document).on('keydown', function (e) {
                            if (e.shiftKey && !app.scenarios.rubberBandActive) {
                                app.scenarios.rubberBandActive = true;
                                app.rx_stand_layer.selectFeature.deactivate();
                                app.rx_stand_layer.selectFeatureBox.activate();
                            }
                        });

                        // reenable click and drag in vectors
                        app.rx_stand_layer.selectFeature.handlers.feature.stopDown = false;
                        map.addControl(app.rx_stand_layer.selectFeature);
                        map.addControl(app.rx_stand_layer.selectFeatureBox);

                    }

                    app.rx_stand_layer.addFeatures(app.geojson_format.read(data));

                    // deactivate the property control
                    app.selectFeature.deactivate();
                    app.rx_stand_layer.selectFeature.activate();
                }
            ),
            // #2 - load the scenario form
            $.ajax({
                url: formUrl,
                type: "GET",
                success: function(data, textStatus, jqXHR) {
                    // Setup the form
                    $('#scenario-form-container').html(data);
                    
                    $('#scenario-form-container').find('button.cancel').click(function(e) {
                        e.preventDefault();
                        self.showScenarioList(true);
                        self.toggleScenarioForm(false);
                        $("form#scenario-form").empty();
                    });
                    $('#scenario-form-container').find('button.submit').click(function(e) {
                        // Submit handler
                        $('#scenario-form-container').prepend("<div class='alert alert-info' id='scenario-form-saving'><h4>Saving...</h4></div>").fadeIn();
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
                                $('#scenario-form-container').html("<h4>Loading...</h4>");
                                var uid = data["X-Madrona-Select"];
                                self.selectedFeatures.removeAll();
                                self.loadScenarios(self.property);
                                self.toggleScenarioForm(false);
                            },
                            error: function(jqXHR, textStatus, errorThrown) {
                                $('#scenario-form-saving').remove();
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
            // #3 - load the list of myrxs 
            $.ajax({
                url: '/features/forestproperty/links/property-myrx-json/' + app.properties.viewModel.selectedProperty().uid() + '/',
                type: "GET",
                dataType: "JSON",
                success: function(res) {
                    app.scenarios.data = {
                        myrxList: res
                    };
                }
            })
        ).then(function() {

            // NOW everything should be ready to roll
            app.scenarios.formViewModel = new scenarioFormViewModel(app.scenarios.data);
            ko.applyBindings(app.scenarios.formViewModel, document.getElementById('scenario-form-container'));

            inrxs_val = $("#id_input_rxs").val();
            if (inrxs_val && edit_mode) {
                // we've got a previously-defined set of rxs
                app.scenarios.formViewModel.inputRxs({});
                var inrxs = JSON.parse(inrxs_val);
                var stand_id;
                var rx_id;
                var myrx;
                var color;
                var stand_feature; 
                var myrx_colors = {};

                // loop through myrxs and transform to a {rx_id: myrx_color} hash
                for (var i = app.scenarios.formViewModel.prescriptionList().length - 1; i >= 0; i--) {
                     myrx = app.scenarios.formViewModel.prescriptionList()[i];
                     myrx_colors[myrx.rx_id] = myrx.color;
                }; 
                // Apply to correct color for each polygon and add to inputRxs 
                for (var i = app.rx_stand_layer.features.length - 1; i >= 0; i--) {
                    stand_feature = app.rx_stand_layer.features[i];
                    stand_id = stand_feature.data.uid.split("_")[2];
                    rx_id = inrxs[stand_id];
                    if (rx_id) {
                        color = myrx_colors[rx_id];
                        stand_feature.attributes.color = color;
                        if (stand_id && rx_id) {
                            app.scenarios.formViewModel.inputRxs()[stand_id] = rx_id;
                        }
                    }
                };
                app.rx_stand_layer.redraw()
                app.scenarios.formViewModel.updateWithRx();
            }
        });
    };

    return self;
}
