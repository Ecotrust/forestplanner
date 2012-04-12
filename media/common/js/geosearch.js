var geosearch = function () {
    var self = this;

    self.searchTerm = ko.observable();
    self.showError = ko.observable(false);
    self.showSpinner = ko.observable(false);

    self.geoSearch = function () {
        var url = '/trees/geosearch';
        self.showError(false);
        self.showSpinner(true);
        $.ajax({
            "url": url,
            "type": "GET",
            "data": { "search": self.searchTerm },
            "success": function (response) {
                var location = new OpenLayers.LonLat(response.center[0], response.center[1]),
                    size = new OpenLayers.Size(21,25),
                    offset = new OpenLayers.Pixel(-(size.w/2), -size.h),
                    icon = new OpenLayers.Icon('http://www.openlayers.org/dev/img/marker.png',size,offset);
                app.markers.addMarker(new OpenLayers.Marker(location,icon.clone()));             
                map.zoomToExtent(OpenLayers.Bounds.fromArray(response.extent));
                self.showError(false);
                self.showSpinner(false);
            },
            "error": function (response) {
                if (response.status === 404) {
                    self.showError(true);
                }
                self.showSpinner(false);
            }
        });
    };

    return self;
};

$(document).ready(function () {
    ko.applyBindings(new geosearch(), document.getElementById('geosearch-form'));
});