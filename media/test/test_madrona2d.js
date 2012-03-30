
module('workspace');

test('load workspace', function () { 
    ok(fixtures.workspace, 'workspace should exist'); 
    ok(fixtures.workspace["generic-links"], 'workspace should have generic links'); 
    ok(fixtures.workspace["feature-classes"], 'workspace should have feature classes'); 
});

test('feature classes', function () {
	var feature_classes = fixtures.workspace["feature-classes"];

	equal(feature_classes.length, 2, "should have two feature classes")
	
});

module('madrona 2d', {
    teardown: function () {
        // unstub $.get
        $.get.restore();
    }
});

asyncTest('load geojson', function () {
	var properties = madrona2d("ForestProperty", fixtures.workspace);

    // stub jquery's ajax function to fake the request
    $.get = sinon.stub($, "get");
    $.get.callsArgWith(1, fixtures.properties);

    properties.load_geojson(function () {
        // get called with specific arguments
        ok($.get.calledOnce);
        equal($.get.getCall(0).args[0], "/trees/user_property_list/");
        equal(properties.geojson, fixtures.properties);

        // return from the async call
        start();
    });

});