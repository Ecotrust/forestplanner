var timemapColorRamp = ["#EDF8E9", "#BAE4B3", "#74C476", "#31A354", "#006D2C"];


var stand_style = {    
    graphicZIndex: 1,
    fillColor: "white",
    fillOpacity: 0,
    strokeWidth: 1,
    strokeOpacity: 1,
    strokeColor: "white",
    strokeDashstyle: "solid"
};

var property_style = {
    graphicZIndex: 999,
    fillOpacity: 0,
    strokeWidth: 2,
    StrokeOpacity: 1,
    strokeColor: "#44FF00",
    strokeDashStyle: "solid",
    label: "${name}",
    labelAlign: "cc",
    fontColor: "#333333",
    fontOpacity: 0.9,
    fontFamily: "Arial",
    fontSize: 14
};

var selected_style = {
    graphicZIndex: 1,
    fillColor: "#44FF00",
    fillOpacity: 0,
    strokeWidth: 2,
    strokeOpacity: 1,
    strokeColor: "yellow"
};

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
                    "Polygon": property_style
                    // "Polygon": {
                        // fillColor: "white",
                        // fillOpacity: 0.5,
                        // strokeWidth: 2,
                        // strokeOpacity: 1,
                        // strokeColor: "#999999",
                        // strokeDashstyle: "dashdot",
                        // label: "${name}",
                        // labelAlign: "cc",
                        // fontColor: "#333333",
                        // fontOpacity: 0.9,
                        // fontFamily: "Arial",
                        // fontSize: 14
                    // }
                }
            })
        ]
    }),
    "select": new OpenLayers.Style(selected_style),
    "temporary": new OpenLayers.Style(null, {
        rules: [
            new OpenLayers.Rule({
                symbolizer: {
                    "Point": {
                        pointRadius: 5,
                        fillColor: "#44ff00"
                    },
                    // "Polygon": stand_style
                    "Polygon": {
                        pointRadius: 5,
                        fillColor: "white",
                        fillOpacity: 0.35,
                        // strokeOpacity: 1,
                        strokeColor: "#444444"
                        // strokeDashstyle: "solid"
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
                        "Polygon": stand_style
                        // "Polygon": {
                            // fillOpacity: 0,
                            // strokeWidth: 1,
                            // strokeOpacity: 0.75,
                            // strokeColor: "white"
                        // }
                    }
                })
            ]
        }),
        "select": new OpenLayers.Style(selected_style),
        // "select": new OpenLayers.Style({
            // graphicZIndex: 1,
            // fillColor: "yellow",
            // fillOpacity: 0.35,
            // strokeWidth: 3,
            // strokeOpacity: 1,
            // strokeColor: "yellow"
        // }),
        "temporary": new OpenLayers.Style(null, {
            rules: [
                new OpenLayers.Rule({
                    symbolizer: {
                        "Point": {
                            pointRadius: 5,
                            fillColor: "#44ff00"
                        },
                        "Polygon": stand_style
                        // "Polygon": {
                            // pointRadius: 5,
                            // fillColor: "white",
                            // fillOpacity: 0.35,
                            // strokeWidth: 2,
                            // strokeOpacity: 1,
                            // strokeColor: "#44ff00"
                        // }
                    }
                })
            ]
        })
    }),

standProperty:
    new OpenLayers.StyleMap(property_style),
    // new OpenLayers.StyleMap({
        // graphicZIndex: 999,
        // fillOpacity: 0,
        // strokeWidth: 2,
        // strokeOpacity: .8,
        // strokeColor: "#44ff00",
        // label: "${name}",
        // labelAlign: "cc",
        // fontColor: "#333333",
        // fontOpacity: 0.9,
        // fontFamily: "Arial",
        // fontSize: 14
    // }),
    
scenarios:
    new OpenLayers.StyleMap({
        "default": new OpenLayers.Style({
            fillColor: "${getColor}",
            fillOpacity: "${getOpacity}", //0.7,
            strokeWidth: 1,
            strokeOpacity: 1,
            strokeColor: '#fff' 

        }, {
            // Rules go here.
            context: {
                getColor: function(feature) {
                    return feature.attributes.color ? feature.attributes.color : "#fff";
                },
                getOpacity: function(feature) {
                    return feature.attributes.color ? 0.5 : 0.0;
                }
            }
        }),
        "select": selected_style
        // "select": {
            // fillOpacity: 0.7,
            // fillColor: "#aaaa00",           //mustard
            // strokeColor: "#ffff00",         //yellow
            // strokeWidth: 2,
            // strokeOpacity: 1.0 
        // }
    }),
    
strataSelect: selected_style,
    // { 
        // fillColor: '#4f0', 
        // fillOpacity: '.6', 
        // strokeColor: '#ff0' 
    // },
    
strataShiftSelect: selected_style
    // { 
        // fillColor: '#4f0', 
        // fillOpacity: '.6', 
        // strokeColor: '#ff0' 
    // }

};

