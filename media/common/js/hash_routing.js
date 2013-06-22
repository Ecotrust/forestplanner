/**
 * Hash Routing and App State 
 * hashChange bound in doc.ready of init.js
 */

//currently used for activating tabs. could be used more generally.
app.state = ko.observable("");

app.hash = "";

app.getState = function () {
    var crumbs = app.breadCrumbs.breadcrumbs(),
		state = crumbs[crumbs.length - 1].url; 
    return state;
};

app.updateUrl = function () {
	return; // believe this is bye bye
    var state = app.getState();
    window.location.hash = state;
};

app.updateUrlProperty = function (uid) {
    var hash = window.location.hash.split("/");
    if (uid) {
        window.location.hash = hash[0] + '/' + uid;
    }
};

// Load state from hash
app.hashChange = function () {
	var loc = window.location.hash.split("/");

	if (loc) {
        //console.info(loc);

        // avoid double triggering, particulary for changing the property_uid in the url
		if (loc[0] === app.hash) {
			console.warn('attempted to load ' + app.hash + ' twice. Ignoring second request.', loc[0], app.hash);
			return;
		}

        switch (loc[0]) {
		case "#properties":
            app.setState.properties(loc);
			break;

		case "#stands":
            // properties already loaded? Deferred alone was slowing things down.
            if (app.properties.viewModel.propertyList().length) {
                app.setState.stands(loc);
            } else {
                $.when(app.properties.viewModel.init()).then(function (resp) {
                    app.setState.stands(loc);
                });
            }
            break;

		case "#scenarios":
            if (app.properties.viewModel.propertyList().length) {
                app.setState.scenarios(loc);
            } else {
                $.when(app.properties.viewModel.init()).then(function (resp) {
                    app.setState.scenarios(loc);
                });
            }
			break;

		case "#about":
			break;
			
		case "#help":
			break;
			
		default:
            // what the? Shh, go to properties.
            app.setState.properties(loc);
			break;
		}
	}
	
	app.hash = loc[0];
	
};

app.setState = {
    properties: function (loc) {
        app.state('properties');

        // if we came from stands, lets hide it. But the model doesn't exist on page load.
        if (app.stands.viewModel !== undefined) {
            app.stands.viewModel.cancelManageStands();
        }
        if (app.scenarios.viewModel !== undefined) {
            app.scenarios.viewModel.cancelManageScenarios();
        }
        if (app.properties.viewModel.propertyList().length < 1) {
            app.properties.viewModel.init();
        } else {
            app.properties.viewModel.showPropertyPanels(true);
        }

    },
    stands: function (loc) {
        app.state('stands');

        // select the current property via the location hash
        // @TODO what if there is no uid?
        app.properties.viewModel.selectPropertyByUID(loc[1]);

        // hide any properties stuff
        // @TODO needs further resetting. could be left in an edit screen.
        app.properties.viewModel.showPropertyList(false);
        app.properties.viewModel.showPropertyPanels(false);

        // if we came from scenarios, hide them.
        if (app.scenarios.viewModel !== undefined) {
            app.scenarios.viewModel.cancelManageScenarios();
        }

        // and go
        app.properties.viewModel.manageStands(app.properties.viewModel);
    },
    scenarios: function (loc) {
        app.state('scenarios');			

        // select the current property via the location hash
        app.properties.viewModel.selectPropertyByUID(loc[1]);

        // if we came from stands, hide them.
        if (app.stands.viewModel !== undefined) {
            app.stands.viewModel.cancelManageStands();
        }
        // hide any properties stuff
        app.properties.viewModel.showPropertyList(false);
        app.properties.viewModel.showPropertyPanels(false);

        // and go
        app.properties.viewModel.manageScenarios(app.properties.viewModel);
    }
};


