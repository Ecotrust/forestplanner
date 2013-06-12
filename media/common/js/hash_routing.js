app.hash = window.location.hash;

app.getState = function () {
    var crumbs = app.breadCrumbs.breadcrumbs();
    var state = crumbs[crumbs.length-1].url; 
    return state;
};

app.updateUrl = function () {
    var state = app.getState();
    window.location.hash = state;
};

// Load state from hash
app.hashChange = function() {
	console.log('**** hashChange');

	//return;

	//var hash = window.location.hash;
	var loc = window.location.hash.split("/");

	if (loc) {
		console.info('loc', loc);

		switch (loc[0]) {
			case "#properties":
				//$('div#home-html,#stand-html, #scenario-html').hide();				
				app.properties.viewModel.init();
				break;
			case "#stands":
				//$('div#home-html,#property-html, #scenario-html').hide();
				//app.stands.viewModel.initialize();
				app.properties.viewModel.manageStands(app.properties.viewModel);
				/* TODO routing stands
				app.properties.viewModel.selectPropertyByUID("trees_forestproperty_123");
				app.properties.viewModel.manageStands();
				$('div#home-html').hide();
				*/
				break;
			case "#scenarios":
				$('div#home-html,#property-html, #stand-html').hide();
				//app.properties.viewModel.init();
				// TODO routing scenarios
				break;
			default:
				app.breadCrumbs.breadcrumbs.push({url: '/', name: 'Home', action: null});
				app.updateUrl();
				break;
		}
	}
};


$(document).ready(function () {
	window.onhashchange = app.hashChange;
	if (window.location.hash) {
		app.hashChange();
	}
});
