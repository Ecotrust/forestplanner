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

// Load state from hash
app.hashChange = function () {
	var loc = window.location.hash.split("/");

	if (loc) {

		if (loc[0] === app.hash) {
			console.warn('loc[0] === app.hash, RETURNING', loc[0], app.hash);
			return;
		}

		switch (loc[0]) {
		case "#properties":
			//app.log("Properties up");
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
			break;


		case "#stands":
			//app.log("Stands up");
			app.state('stands');			

			if (app.properties.viewModel !== undefined) {
				app.properties.viewModel.showPropertyList(false);
				app.properties.viewModel.showPropertyPanels(false);
			}
			if (app.scenarios.viewModel !== undefined) {
				app.scenarios.viewModel.cancelManageScenarios();
			}
			app.properties.viewModel.manageStands(app.properties.viewModel);
			break;

		case "#scenarios":
			//app.log("Scenarios up");
			app.state('scenarios');			

			if (app.stands.viewModel !== undefined) {
				app.stands.viewModel.cancelManageStands();
			}
			if (app.properties.viewModel !== undefined) {
				app.properties.viewModel.showPropertyList(false);
				app.properties.viewModel.showPropertyPanels(false);
			}
			app.properties.viewModel.manageScenarios(app.properties.viewModel);

			break;

		default:
			app.state('properties');
			// TODO? Set window.hash to #properties and move on? Recursion?
		
			// if we came from stands, lets hide it. But the model doesn't exist on page load.
			if (app.stands.viewModel !== undefined) {
				//app.stands.viewModel.showStandPanels(false);
				app.stands.viewModel.cancelManageStands();
			}
			// if we came from scenarios, lets hide it. But the model doesn't exist on page load.
			if (app.scenarios.viewModel !== undefined) {
				app.scenarios.viewModel.cancelManageScenarios();
			}
			break;
		}
	}
	
	app.hash = loc[0];
	
};


$(document).ready(function () {
	//window.onhashchange = app.hashChange;
	//if (window.location.hash) {
		//app.hashChange();
	//}
});


