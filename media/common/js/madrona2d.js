var madrona2d = function(feature_title, workspace, layer, add_layer, viewModel) {
    var exports = {
        geojson: null
    };

    exports.load_geojson = function (callback) {
        return $.get('/trees/user_property_list/', function (data) {
            exports.geojson = data;
            callback();
        });
    };

    return exports;
};
