var timemapColorRamp = ["#EDF8E9", "#BAE4B3", "#74C476", "#31A354", "#006D2C"];

var map_styles = {
    
drawn: 
    new OpenLayers.StyleMap({
    "default": new OpenLayers.Style(null, {
        rules: [
            new OpenLayers.Rule({
                symbolizer: {
                    "Polygon": {
                        fillColor: "white",
                        fillOpacity: 0.35,
                        strokeWidth: 2,
                        strokeOpacity: 1,
                        strokeColor: "#444444"
                    }
                }
            })
        ]
    }),
    "select": new OpenLayers.Style({
        strokeColor: "#44ff00"
    }),
    "temporary": new OpenLayers.Style(null, {
        rules: [
            new OpenLayers.Rule({
                symbolizer: {
                    "Point": {
                        pointRadius: 5,
                        fillColor: "#44ff00"
                    },
                    "Polygon": {
                        pointRadius: 5,
                        fillColor: "white",
                        fillOpacity: 0.35,
                        strokeWidth: 2,
                        strokeOpacity: 1,
                        strokeColor: "#44ff00"
                    }
                }
            })
        ]
    })
}),

forestProperty: 
    new OpenLayers.StyleMap({
    "default": new OpenLayers.Style(null, {
        rules: [
            new OpenLayers.Rule({
                symbolizer: {
                    "Polygon": {
                        fillColor: "white",
                        fillOpacity: 0.35,
                        strokeWidth: 2,
                        strokeOpacity: 1,
                        strokeColor: "#999999",
                        strokeDashstyle: "dashdot",
                        label: "${name}",
                        labelAlign: "cc",
                        fontColor: "#333333",
                        fontOpacity: 0.9,
                        fontFamily: "Arial",
                        fontSize: 14
                    }
                }
            })
        ]
    }),
    "select": new OpenLayers.Style({
        strokeColor: "#444444",
        fillOpacity: 0.12
    }),
    "temporary": new OpenLayers.Style(null, {
        rules: [
            new OpenLayers.Rule({
                symbolizer: {
                    "Point": {
                        pointRadius: 5,
                        fillColor: "#44ff00"
                    },
                    "Polygon": {
                        pointRadius: 5,
                        fillColor: "white",
                        fillOpacity: 0.35,
                        strokeOpacity: 1,
                        strokeColor: "#444444",
                        strokeDashstyle: "solid"
                    }
                }
            })
        ]
    })
}),

stand:
    new OpenLayers.StyleMap({
        "default": new OpenLayers.Style(null, {
            rules: [
                new OpenLayers.Rule({
                    symbolizer: {
                        "Polygon": {
                            fillOpacity: 0,
                            strokeWidth: 1,
                            strokeOpacity: 0.75,
                            strokeColor: "white"
                        }
                    }
                })
            ]
        }),
        "select": new OpenLayers.Style({
            graphicZIndex: 1,
            fillColor: "white",
            fillOpacity: 0.18,
            strokeWidth: 3,
            strokeOpacity: 1,
            strokeColor: "yellow"
        }),
        "temporary": new OpenLayers.Style(null, {
            rules: [
                new OpenLayers.Rule({
                    symbolizer: {
                        "Point": {
                            pointRadius: 5,
                            fillColor: "#44ff00"
                        },
                        "Polygon": {
                            pointRadius: 5,
                            fillColor: "white",
                            fillOpacity: 0.35,
                            strokeWidth: 2,
                            strokeOpacity: 1,
                            strokeColor: "#44ff00"
                        }
                    }
                })
            ]
        })
    }),

standProperty:
    new OpenLayers.StyleMap({
        fillOpacity: 0,
        strokeWidth: 2,
        strokeOpacity: 1,
        strokeColor: "#44ff00"
    }),
    
scenarios:
    new OpenLayers.StyleMap({
        "default": new OpenLayers.Style({
            fillColor: "${getColor}",
            fillOpacity: "${getOpacity}", //0.7,
            strokeWidth: 1,
            strokeOpacity: 0.6

        }, {
            // Rules go here.
            context: {
                getColor: function(feature) {
                    return feature.attributes.color ? feature.attributes.color : "#fff";
                },
                getOpacity: function(feature) {
                    return feature.attributes.color ? 0.7 : 0.0;
                }
            }
        }),
        "select": {
            fillOpacity: 0.7,
            fillColor: "#aaaa00",
            strokeColor: "#ffff00",
            strokeWidth: 2,
            strokeOpacity: 1.0 
        }
    })

};

