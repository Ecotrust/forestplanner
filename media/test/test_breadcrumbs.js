
module('breadcrumbs', {
    teardown: function () {
        app.breadCrumbs.breadcrumbs.removeAll();
    }
});

test('test isLast', function () { 
    // set up the breadcrumbs
    app.breadCrumbs.breadcrumbs.push({url: '/url', name: 'name'});
    app.breadCrumbs.breadcrumbs.push({url: '/url', name: 'name'});

    ok(! app.breadCrumbs.isLast(app.breadCrumbs.breadcrumbs()[0]), 'should be the last breadcrumb');

    ok(app.breadCrumbs.isLast(app.breadCrumbs.breadcrumbs()[1]), 'should be the last breadcrumb');

});

module('update', {
    setup: function () {
        // setup the breadcrumbs
        app.breadCrumbs.breadcrumbs([
            {url: '/', name: 'Home'},
            {url: '/properties', name: "Properties"},
            {url: '/properties/forest-moon', name: "Forest Moon"}]);

    }, 
     teardown: function () {
        app.breadCrumbs.breadcrumbs.removeAll();
    }
});

test('test update', function () {
    
    // update should start from the first level and look for a match
    // when it finds a common ancestor, throw the rest away
    app.breadCrumbs.update({url: '/', name: "Home"});
    equal(app.breadCrumbs.breadcrumbs().length, 1, 'should only have one item');
    strictEqual(app.breadCrumbs.breadcrumbs()[0].url, '/', 'should just be /');
    strictEqual(app.breadCrumbs.breadcrumbs()[0].name, 'Home', 'should just be Home');

});

test('update at second level', function () {
    app.breadCrumbs.update({url: '/properties', name: "Properties"});
    equal(app.breadCrumbs.breadcrumbs().length, 2, 'should only have two items');
    strictEqual(app.breadCrumbs.breadcrumbs()[1].url, '/properties', 'should match given url');
    strictEqual(app.breadCrumbs.breadcrumbs()[1].name, 'Properties', 'should match given name');    
})

test('update at top level', function () {
    app.breadCrumbs.update({url: '/property', name: "Endor"});
    equal(app.breadCrumbs.breadcrumbs().length, 3, 'should have three items');
    strictEqual(app.breadCrumbs.breadcrumbs()[2].url, '/properties', 'should match given url');
    strictEqual(app.breadCrumbs.breadcrumbs()[2].name, 'Properties', 'should match given name');    
});