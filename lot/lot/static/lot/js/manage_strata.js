var madrona = {
    onShow: function (callback) {
        callback();
        //madrona.formCallbacks.push(callback);
    },
    formCallbacks: [],
    features: {}
};

var app = {
    stands: {},
    scenarios: {},
    properties: {}
};

if (context.user.is_authenticated) {
  $.get('/features/' + context.user.username + '/workspace-owner.json', function (data) {
    app.workspace = data;
  });
} else {
  $.get('/features/workspace-public.json', function (data) {
    app.workspace = data;
  });
}

app.helpText = ko.observable();
$.get('/trees/intro.html', function(text){
    app.helpText($(text).find('#intro-vegetation')[0].outerHTML);
});

// call array.cycle(x) to extend the array to x elements
// by cycling through. if x < length, return original array
Array.prototype.cycle = function(val){
    var l = this.length;
    if(l < val){
        for(var i = val-1-l; i >= 0; i--){
            this[i+l] = this[i % l];
        }
    }
    return this;
};

var colorRamp = ['D8E2A7','DA9C90','D2A379','CCC266','ADD071','6AC247','339936','267373','349D7F','449FC1','6A86CD','7971D0','AB81D5','C79FDF','EBC6EC'];
colorRamp = colorRamp.cycle(50); // support up to 50 forest types

// to go into strata.js
app.strata = {
    property_id: context.property_id,
    property_name: context.property_name,
    property_is_locked: context.property_is_locked,
    color: colorRamp,
    treeSpecies : ko.observableArray(),
    sizeClasses : []
};

app.strata.colorMap = {};
app.strata.init = function () {
    app.strata.viewModel = new strataViewModel();

    $.each(app.strata.data, function (i, strata) {
      app.strata.viewModel.strataList.push(new stratumViewModel(strata));
    });

    ko.applyBindings(app.strata.viewModel);

    // add controls, save references
    app.selectFeature = new OpenLayers.Control.SelectFeature(app.stand_layer, {
            "clickout": false,
            "multiple": true,
            "toggle": true,
            //styling here to ensure selecting stands
            // with strata applied appear selected.
            "selectStyle": map_styles.strataSelect //defined in styles.js
    });

    map.render('map');
    map.updateSize();
    map.zoomToExtent(app.property_layer.getDataExtent());

    $('.info-help').find('strong')
        .next('span').hide()
        .after('<span class="read-more"> Read More...</span>');

    $('.info-help .read-more').on('click', function () {
        var $t = $(this);
        // console.log('$t clicked', $t);
        $t.prev('span').toggle();
        $t.closest('.info-help').toggleClass('opened');
        if ($t.prev('span').is(':visible')) {
            $t.text(' Read Less');
        } else {
            $t.text(' Read More...');
        }
    });

    // reenable click and drag in vectors
    map.addControl(app.selectFeature);
    app.selectFeature.activate();
};

// individual stand list member
function standViewModel (stratum, options) {
    var self = this, chartTimer = null;
    if (! options) {
      options = [];
    }
    // reference to the parent stratum
    self.stratum = stratum;

    // stand characteristics
    self.species = ko.observable(options[0]);
    self.tpa = ko.observable('22');
    if (options[1] && options[2]) {
      self.sizeClass = ko.observable([options[1] + '"', options[2] + '"'].join(' to '));
    } else {
      self.sizeClass = ko.observable();
    }

    if (options[3]) {
      self.tpa = ko.observable(parseInt(options[3], 10));
    } else {
      self.tpa = ko.observable();
    }
    //self.percentage = ko.observable(  );

    self.percentage = ko.computed(function () {
        var self = this;
        return Math.ceil(( (self.tpa() / self.stratum.totalTpa()) * 100).toFixed(0));
    }, self);

    self.percentageIsValid = ko.observable(true);
    self.percentageIsValidMsg = ko.observable('');

    self.index = ko.computed(function () {
        var self = this;
        return stratum.standList.indexOf(this);
    }, self);

    self.updateChart = function () {
      // delay the chart update for a bit
      if (chartTimer) {
        clearTimeout(chartTimer);
      }
      chartTimer = setTimeout(function () {
        app.strata.chartStandList(self.stratum.displayStandList());
      }, 500);
    };

    self.isEditing = ko.observable(false);
    self.speciesConfirmDelete = ko.observable(false);
    self.editTree = function (event) {
        this.isEditing(true);
    };

    self.updateTree = function (task) {
        //create the new model and push to standList here?
        this.isEditing(false);
        app.strata.viewModel.activeStratum().recalculateDisplayStandList.notifySubscribers();
    };

    self.sizeClasses = ko.computed(function() {
            var pos = app.strata.treeSpecies().indexOf(self.species());
            return app.strata.sizeClasses[pos-1];
    }, self);

    self.percentage.subscribe(self.updateChart);
    self.species.subscribe(self.updateChart);
    self.sizeClass.subscribe(self.updateChart);

    return self;
};


// viewmodel for a single stratum (aka Forest Type)
function stratumViewModel (options) {
    var self = {};

    if (! options) {
        options = {};
    }
    // console.dir(options);
    self.attributes = {
        // feature attributes from madrona
        name: ko.observable(options.name),
        search_tpa: ko.observable(options.search_tpa),
        search_age: ko.observable(options.search_age),
        additional_desc: ko.observable(options.additional_desc),
        stand_list: ko.observable(options.stand_list),
        uid: options.uid
    };

    // viewmodel attributes
    self.color = ko.observable();
    self.currentStand = ko.observable();
    self.confirmDelete = ko.observable(false);
    self.editMode = ko.observable(false);
    self.editTrees = ko.observable(false);

    self.standList = ko.observableArray();

    self.species = ko.observable();
    self.sizeClass = ko.observable();
    self.percentage = ko.observable();
    self.tpa = ko.observable();

    self.totalTpa = ko.computed(function(){
        var totalTpa = 0;

        $.each(self.standList(), function(i, stand){
            // console.info('stand.tpa()', stand.tpa());
            totalTpa += parseInt(stand.tpa(), 10);
        });
        return totalTpa;
    });

    self.saveTreee = function (tree, event, bar) {
        if(tree){
            tree.isEditing(false);
            self.standList.remove(tree);
            self.standList.push(tree);
            app.strata.viewModel.activeStratum().recalculateDisplayStandList.notifySubscribers();
        }
    };

    self.showTrees = ko.observable(false);

    self.toggleTrees =  function(){
         self.showTrees(!self.showTrees());
    };

    self.totalPercentage = ko.computed(function(){
        var totalPercentage = 0;

        $.each(self.standList(), function(i, stand){
            totalPercentage += parseInt(stand.percentage(), 10);
        });
        return totalPercentage;
    });

    // basic validation setup. More @TODO
    // check for numbers, display errors...
    self.canSave = ko.computed(function(){
        var canSave = true;

        if ( !self.attributes.name() ) {
            canSave = false;
        }
        if ( !self.attributes.search_age() ) {
            canSave = false;
        }

        return canSave;
    });

    self.recalculateDisplayStandList = ko.observable();


    // display a computed standlist with a dummy last item
    // to show the remaining percentage
    // called on keyup when model changes at all
    self.displayStandList = ko.computed(function () {
        var displayStandList = [], totalPercentage = 0, msg;

        // cheap hax. When saving a standlist member,
        // we ping recalculateDisplayStandList so displayStandlist
        // updates itself. without it, we don't get the
        // remaining % species placeholder added again.
        self.recalculateDisplayStandList();

        $.each(self.standList(), function (i, stand) {
            displayStandList.push(stand);
        });

        if ( app.strata.viewModel.activeStratum() &&
            (app.strata.viewModel.activeStratum().attributes.name() == self.attributes.name())){
            // species name, sizeclass lower bound, upper bound, percentage
            var placeHolder = new standViewModel(self,
            //[ 'Unknown type', "?", "?", 100 - totalPercentage ]);
            [ 'Unknown type', "?", "?", 0 ]);

            placeHolder.isEditing(true);

            displayStandList.push(placeHolder);

            if( app.strata.viewModel.activeStratum().attributes.uid == self.attributes.uid ){
                // self.standList.push(placeHolder);
            }
        }

        return displayStandList;
    });


    if (options.stand_list) {
      $.each(options.stand_list.classes || JSON.parse(options.stand_list).classes, function (i, stand) {

        // console.warn('pushed new standViewModel from options.stand_list');
        self.standList.push(new standViewModel(self, stand));
      });
    }

    // set the color and store a reference
    if (self.attributes.uid != undefined && app.strata.colorMap[self.attributes.uid]) {
        self.color(app.strata.colorMap[self.attributes.uid]);
    } else {
        self.color('#' + app.strata.color.reverse().pop());
        app.strata.colorMap[self.attributes.uid] = self.color(); //TODO: app.strata.colorMap['undefined'] is being set. This should probably be fixed
    }

    // initial stand coloring
    $.each(app.stand_layer.features, function(i, stand) {
        // @TODO: if you have 10 strata and 15 stands, this is running 150 times.
        // better way?
        if (stand.attributes.strata !== null && stand.attributes.strata.uid === self.attributes.uid) {
            stand.style = {
                fillColor: self.color(),
                fillOpacity: '.6',
                strokeColor: '#fff'
            };
            app.stand_layer.drawFeature(stand);
            app.strata.viewModel.setAppliedStrataTotal();
        }
    });

    self.deleteStratum = function(stratum) {
        app.strata.deleteStratum(stratum.attributes.uid, function() {
            app.strata.viewModel.strataList.remove(stratum);
            self.clearStands(stratum.attributes.uid);
        });
    };


    //when a stratum is deleted, make sure we clear the existing stands on the map as well
    self.clearStands = function(uid) {
        $.each(app.stand_layer.features, function(i, feature) {
            // is it a stand assigned to the deleted stratum?
            if (feature.attributes.strata !== null && feature.attributes.strata.uid === uid) {
                //clear and apply
                feature.style = {
                    fillColor: 'Transparent',
                    fillOpacity: '.6',
                    strokeColor: '#fff'
                };
                feature.attributes.strata = null;
                feature.data.strata = null;
                app.stand_layer.drawFeature(feature);

                //hey count, pay attention.
                app.strata.viewModel.setAppliedStrataTotal();
            }
        });
    };

    self.addSpecies = function(stand, event) {
        var stand,
            self = this,
            attrs = [],
            sizes;

        //sizes = '24" to 36"' - remove quotes and split
        sizes = self.sizeClass().replace(/(")/g, "").split(" to ");

        // 139% sure there is a better way.
        attrs[0] = self.species();
        attrs[1] = sizes[0];
        attrs[2] = sizes[1];
        attrs[3] = self.percentage();

        stand = new standViewModel(self, attrs);

        self.species('');
        self.percentage('');

        self.standList.push(stand);

        console.warn('pushed new standViewModel from self.addSpecies');
        self.currentStand(stand);
        self.currentStand().updateChart();
    };


    self.removeSpecies = function(stand) {
        self.standList.remove(stand);
    };


    self.sizeClasses = ko.computed(function() {
        var pos = app.strata.treeSpecies().indexOf(self.species());
        return app.strata.sizeClasses[pos - 1];
    }, self);


    ko.bindingHandlers.select2 = {
        init: function(element, valueAccessor, allBindingsAccessor) {
            var obj = valueAccessor(),
                allBindings = allBindingsAccessor(),
                lookupKey = allBindings.lookupKey;

            $(element).select2(obj);

            if (lookupKey) {
                var value = ko.utils.unwrapObservable(allBindings.value);
                $(element).select2('data', ko.utils.arrayFirst(obj.data.results, function(item) {
                    return item[lookupKey] === value;
                }));
            }

            ko.utils.domNodeDisposal.addDisposeCallback(element, function() {
                $(element).select2('destroy');
            });
        },
        update: function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext) {
            //$(element).trigger('change');

            if (!self.currentStand()) {
                var stand = new standViewModel(self);
                self.currentStand(stand);
            }


        }
    };

    // console.dir(self.standList());

    return self;
    };




    function strataViewModel() {
        var self = {};

        // filter term for strata
        self.searchTerm = ko.observable();
        // list of strata
        self.strataList = ko.observableArray();
        self.vegetationTypeError = ko.observable(null);
        self.standTotal = app.stand_layer.features.length;

        // n of Y stands applied
        self.appliedStrataTotal = ko.observable(0);
        self.setAppliedStrataTotal = function() {
            var total = 0;

            $.each(app.stand_layer.features, function(i, stand) {
                if (stand.attributes.strata !== null) {
                    total = total + 1;
                }
            });
            self.appliedStrataTotal(total);

        };

        // either false, or holds a stratumViewModel
        self.activeStratum = ko.observable();

        // the species lists needs an empty string at the beggining
        self.treeSpecies = app.strata.treeSpecies;
        self.treeSpecies.unshift('');

        // strata list that is actually displayed on the page
        // filtered by searchTerm
        self.filteredStrataList = ko.computed(function() {
            var strataList = this,
                filteredStrataList = [],
                searchTerm;

            if (self.searchTerm()) {
                searchTerm = self.searchTerm().toLowerCase();

                // filter the strata list
                $.each(strataList(), function(i, strata) {

                    // if (strata.attributes.name().toLowerCase().indexOf(searchTerm) !== -1 || strata.attributes.stand_list().toLowerCase().indexOf(searchTerm) !== -1) {
                    if (strata.attributes.name().toLowerCase().indexOf(searchTerm) !== -1) {
                        filteredStrataList.push(strata);
                    }
                });
            } else {
                filteredStrataList = strataList();
            }
            return filteredStrataList;
        }, self.strataList);

        self.clearStandFilter = function() {
            self.searchTerm("");
        };

        self.activeStratum.subscribe(function(activeStratum) {

            if (activeStratum && activeStratum.standList().length) {
                app.strata.chartStandList(activeStratum.displayStandList());
            } else { // no active stratum, so set cached chart data to null
                app.strata.chartData = null;
            }

        });

        self.strataList.subscribe(function() {
            self.setAppliedStrataTotal();
        });

        self.rubberBandActive = ko.observable(false);

        app.selectFeature = new OpenLayers.Control.SelectFeature(app.stand_layer, {
            "clickout": false,
            "multiple": true,
            "toggle": true,
            "selectStyle": map_styles.strataSelect
        });

        app.selectFeatureBox = new OpenLayers.Control.SelectFeature(app.stand_layer, {
            "clickout": false,
            "multiple": true,
            "toggle": true,
            "box": true,
            "selectStyle": map_styles.strataShiftSelect
        });

        $(document).on('keydown', function(e) {
            if (e.shiftKey && !self.rubberBandActive()) {
                self.rubberBandActive(true);
                app.selectFeature.deactivate();
                app.selectFeatureBox.activate();
            }
        });

        $(document).on('keyup', function(e) {
            if (self.rubberBandActive()) {
                self.rubberBandActive(false);
                app.selectFeatureBox.deactivate();
                app.selectFeature.activate();
            }
        });

        map.addControl(app.selectFeature);
        map.addControl(app.selectFeatureBox);

        self.editStratum = function(stratum) {
            // var duplicateStratum = new stratumViewModel(ko.toJS(stratum.attributes));
            // duplicateStratum.editMode(true);
            // self.activeStratum(duplicateStratum);
            app.strata.stratumBeingEdited = stratum;
            stratum.editMode(true);
            self.activeStratum(stratum);
            window.location.hash = 'edit-vegetation-type';
        };

        self.cancel = function() {
            self.activeStratum(null);
            self.vegetationTypeError(null);
            map.render('map');
        };

        self.createStratum = function() {
            console.warn('createStratum');
            self.activeStratum(new stratumViewModel());
        };

        self.applyStrata = function(stratum) {
            // can be called from the draggable/droppable
            // switching to the knockout binding for now
            var stand_uid_list = [],
                color = stratum.color(),
                stratum_id = stratum.attributes.uid;

            // get strata id, if knockout stratum will be this

            // Do we have a strata selected?
            // @TODO more KO, less JQ
            if (!app.stand_layer.selectedFeatures.length) {

                var msg = "Please select a stand on your map to apply this forest type.",
                    $t;

                // little clean up because DOM stuff is silly
                $('.stratum-box .alert-error').remove();

                // add and remove a temporary warning
                $('[data-sid="' + stratum_id + '"]').prepend('<div class="alert-error">' + msg + '</div>')
                    .find('.alert-error').each(function() {
                        $t = $(this);
                        window.setTimeout(function() {
                            $t.fadeOut(1300, function() {
                                $t.remove();
                            });
                        }, 5000);
                    });

                return;
            }

            // apply strata to selected stands
            $.each(app.stand_layer.selectedFeatures, function(i, feature) {
                // don't count features already counted
                if (!feature.attributes.strata) {
                    // var currentTotal = self.appliedStrataTotal();
                    // self.appliedStrataTotal(currentTotal+1);
                }
                feature.style = {
                    fillColor: color,
                    fillOpacity: '.6',
                    strokeColor: '#fff'
                };
                feature.attributes.strata = ko.mapping.toJS(stratum.attributes);
                feature.data.strata = ko.mapping.toJS(stratum.attributes);

                app.stand_layer.drawFeature(feature);
                stand_uid_list.push(feature.attributes.uid);
            });

            app.strata.applyStrataToStand(stratum_id, stand_uid_list);
            app.selectFeature.unselectAll();
            self.setAppliedStrataTotal();
        };

        self.updateStratum = function(oldStratum, activeStratum) {
            console.warn('updateStratum');
            self.strataList.replace(oldStratum, new stratumViewModel(activeStratum));
        };


        self.saveStrata = function(data, event) {


            var self = this,
                postData,
                stratum = app.strata.viewModel.activeStratum(),
                url = "/features/strata/form/",
                $target = $(event.target),
                $targetText = $target.text();


            if (!stratum.canSave()) {
                self.vegetationTypeError("Please include a name and age for this Forest Type.");
                return;
            }

            $target.addClass('loading').text('Saving. One moment...');

            self.vegetationTypeError(null);

            if (stratum.editMode()) {
                url = "/features/strata/{uid}/".replace('{uid}', stratum.attributes.uid);
            }

            stratum.attributes.search_tpa(stratum.totalTpa());
            postData = ko.mapping.toJS(stratum.attributes);

            postData.stand_list = ko.toJSON({
                'property': app.strata.property_id,
                'classes': $.map(stratum.standList(), function(stand) {
                    var sizes = [];

                    if (stand.species() && stand.sizeClass() && stand.tpa()) {
                        sizes = stand.sizeClass().replace(/(")/g, "").split(" to ");

                        return [
                            [
                                stand.species(),
                                parseInt(sizes[0], 10),
                                parseInt(sizes[1], 10),
                                parseInt(stand.tpa())
                            ]
                        ];
                    }
                })
            });

            $.ajax(
              {
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                },
                url: url,
                type: "post",
                traditional: true,
                datatype: 'json',
                data: postData,
                success: function(response) {

                    if (typeof(response) == "string") {
                        response = jQuery.parseJSON(response);
                    }

                    var strata_uid = response["X-Madrona-Select"];

                    if (stratum.editMode()) {
                        // existing strata
                        self.updateStratum(app.strata.stratumBeingEdited, postData);
                    } else {
                        // new strata
                        app.strata.associateStandWithProperty(app.strata.property_uid, strata_uid);
                        self.activeStratum().attributes.stand_list = postData.stand_list;
                        self.activeStratum().attributes.uid = strata_uid;
                        self.strataList.push(self.activeStratum());
                    }
                    self.activeStratum(null);
                    self.vegetationTypeError(null);
                    map.render('map');


                },
                error: function(response) {
                    var msg = "";
                    if (response.status == 400) {
                        //@TODO er, ko. -wm
                        msg = "We were unable to find a representative plot for your inventory. please verify ";
                        msg += "the species and size classes you've entered. if everything looks ok, ";
                        msg += "please try to remove any minor species or diameter classes from your list. ";
                        msg += "\n\n" + "The forest scenario planner is in active development - ";
                        msg += "please let us know if we can help via the about page above.";
                        self.vegetationTypeError(msg);
                    } else {
                        msg = "we're sorry, something has gone wrong with saving your forest type; please check your work and try again. ";
                        msg += "\n\n" + "if you continue to have trouble ";
                        msg += "saving your forest type, please contact us with this error code: " + response.status;
                        msg += " via the about page above. thank you.";
                        self.vegetationTypeError(msg);
                    }
                },
                complete: function() {
                    $target.removeClass('loading').text($targetText);
                }

            });
        };

        return self;
    }



    app.strata.deleteStratum = function(strata_uid, cb) {
        var url = "/features/generic-links/links/delete/{strata_uid}/".replace('{strata_uid}', strata_uid);

        return $.ajax({
            url: url,
            type: "DELETE",
            traditional: true,
            success: function(response) {
                cb();
            },
            error: function(response) {
                console.log(response);
            }
        });
    };

    app.strata.applyStrataToStand = function(strata_uid, stand_uid_list) {
        var url = "/features/strata/links/add-stands/{strata_uid}/".replace('{strata_uid}', strata_uid);

        return $.ajax({
            url: url,
            type: "POST",
            data: {
                'stands': stand_uid_list.join()
            },
            traditional: true,
            success: function(response) {

            },
            error: function(response) {

            }
        });
    };

    app.strata.associateStandWithProperty = function(property_uid, strata_uid) {
        var url = "/features/forestproperty/{property_uid}/add/{strata_uid}";

        url = url.replace('{property_uid}', app.strata.property_id);
        url = url.replace('{strata_uid}', strata_uid);

        return $.ajax({
            url: url,
            type: "POST",
            traditional: true,
            success: function(response) {

            },
            error: function(response) {

            }
        });
    };


    $.when(
        $.getJSON("/features/forestproperty/links/property-strata-list/" + app.strata.property_id + '/', function(data) {
            app.strata.data = data;
        }),

        //get the actual available species
        $.getJSON("/trees/variant/" + app.strata.property_id + "/species_sizecls.json", function(data) {
            //should probably be done server side.
            classes = data.classes;
            classes.sort(function(a, b) {
                if (a.species < b.species) return -1;
                if (a.species > b.species) return 1;
                return 0;
            });
            $.each(classes, function(i, tree) {
                var sizes = $.map(tree.size_classes, function(a, i) {
                    //return [[a.min, a.max]];
                    return a.min.toString() + '" to ' + a.max.toString() + '"';
                });
                app.strata.treeSpecies.push(tree.species);
                app.strata.sizeClasses.push(sizes);
            });
        }),

        $.get('/features/generic-links/links/geojson/{uid}/'.replace('{uid}', app.strata.property_id), function(data) {
            app.property_layer.addFeatures(app.geojson_format.read(data));

        }),
        $.get('/features/forestproperty/links/property-stands-geojson/{property_id}/'.replace('{property_id}', app.strata.property_id), function(data) {
            //var styleMap = map_styles.stand;
            app.stand_layer = new OpenLayers.Layer.Vector("Stands", {
                styleMap: map_styles.stand,
                renderers: app.renderer
            });

            app.stand_layer.styleMap.default = new OpenLayers.Style({
                fillColor: "blue",
            }, {
                // Rules go here.
                context: {}
            });
            map.addLayer(app.stand_layer);
            app.stand_layer.addFeatures(app.geojson_format.read(data));
        })
    ).then(function() {
        app.strata.init();
    });




    // charting stuff
    app.strata.chartData = null;
    app.strata.chartTimer = null;

    app.strata.chartStandList = function(standList) {
        var chart, chartData, chartDataUpdated = true;
        if (app.strata.chartTimer) {

        }
        chartData = $.map(standList, function(stand) {
            var sizeClass = stand.sizeClass() ? (' ' + stand.sizeClass()) : null;
            if (stand.percentage()) {
                return [
                    [
                        stand.species() + ' ' + sizeClass,
                        parseInt(stand.percentage(), 10)
                    ]
                ];
            }
        });
        // check to see if data has been udpated
        if (app.strata.chartData && ko.toJSON(chartData) === ko.toJSON(app.strata.chartData)) {
            chartDataUpdated = false;
        }
        if (chartDataUpdated && app.strata.viewModel.activeStratum()) {
            setTimeout(function() {
                app.strata.chartData = chartData;
                chart = new Highcharts.Chart({
                    chart: {
                        renderTo: 'chart-container',
                        plotBackgroundColor: null,
                        plotBorderWidth: null,
                        plotShadow: false,
                        backgroundColor: 'rgba(255, 255, 255, 0.1)'
                    },
                    title: {
                        text: 'Species Breakdown',
                        css: {
                            fontFamily: 'Helvetica,Arial,sans-serif'
                        }
                    },
                    credits: false,
                    tooltip: {
                        pointFormat: '{series.name}: <b>{point.percentage:.2f}%</b>',
                        percentageddDecimals: 1,
                        valueDecimals: 2
                    },
                    plotOptions: {
                        pie: {
                            allowPointSelect: true,
                            cursor: 'pointer',
                            dataLabels: {
                                enabled: false,
                                color: '#000000',
                                connectorColor: '#000000',
                                formatter: function() {
                                    return '<b>' + this.point.name + '</b>: ' + (this.percentage).toFixed(0) + ' %';
                                }
                            }
                        }
                    },
                    series: [{
                        type: 'pie',
                        name: 'Percentage',
                        data: chartData
                    }]

                });
            }, 300);
        }
    };
