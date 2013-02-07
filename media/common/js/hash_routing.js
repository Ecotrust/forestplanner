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
    
$(document).ready(function() {
    if (app.hash) {
        // Load state from hash
        var loc = app.hash.split("/");
        switch(loc[0]) {
            case "#properties":
                $('div#home-html').hide();
                app.properties.viewModel.init();
                break;
            case "#stands":
                $('div#home-html').hide();
                app.properties.viewModel.init();
                /* TODO routing stands
                app.properties.viewModel.selectPropertyByUID("trees_forestproperty_123");
                app.properties.viewModel.manageStands();
                $('div#home-html').hide();
                */
                break;
            case "#scenarios":
                $('div#home-html').hide();
                app.properties.viewModel.init();
                // TODO routing scenarios
                break;
            default:
                console.log("Going home");
                app.breadCrumbs.breadcrumbs.push({url: '/', name: 'Home', action: null});
                app.updateUrl();
                break;
        }
    }
});
