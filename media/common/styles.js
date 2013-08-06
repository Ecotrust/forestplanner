var timemapColorRamp = ["#EDF8E9", "#BAE4B3", "#74C476", "#31A354", "#006D2C"];


var stand_style = {    
    graphicZIndex: 1,
    fillColor: "white",
    fillOpacity: 0.3,
    strokeWidth: 1,
    strokeOpacity: 0.8,
    strokeColor: "white",
    strokeDashstyle: "solid"
};

var property_style = {
    graphicZIndex: 999,
    pointRadius: 5,
    fillOpacity: 0.1,
    fillColor: "#FFFFFF",
    strokeWidth: 2,
    StrokeOpacity: 1,
    strokeColor: "white", //"#44FF00",
    strokeDashStyle: "solid",
    label: "${name}",
    labelAlign: "cc",
    fontColor: "#333333",
    fontOpacity: 0.9,
    fontFamily: "Arial",
    fontSize: 14
};

var selected_prop_style = {
    graphicZIndex: 1,
    fillColor: "#FFFFFF", //"#FFA000",
    fillOpacity: 0.2,
    strokeWidth: 4,
    strokeOpacity: 1,
    strokeColor: "#FFFFFF" //"#FFA000"
};

var selected_stand_style = {
    graphicZIndex: 9999,
    fillColor: "#44FF00", //"#FFA000",    
    fillOpacity: 0.4,
    strokeWidth: 5,
    strokeOpacity: 0.7,
    strokeColor: "#44FF00",
};

var def_symbolizer_style = {
    "Polygon": {
        pointRadius: 5,
        fillColor: "#44FF00",
        fillOpacity: 1,
        strokeWidth: 2,
        strokeOpacity: 1,
        strokeColor: "white"
    }
};

var temp_symbolizer_style = {
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

var time_map_template = {
    fillOpacity: 0.8,
    strokeColor: "#FFFFFF",
    strokeWidth: 1,
    fillColor: "${getColour}"
};

var map_styles = {
    
drawn: 
    new OpenLayers.StyleMap({
        "default": new OpenLayers.Style(null, {
            rules: [
                new OpenLayers.Rule({
                    symbolizer: def_symbolizer_style
                })
            ]
        }),
        "select": new OpenLayers.Style({
            strokeColor: "#44ff00"
        }),
        "temporary": new OpenLayers.Style(null, {
            rules: [
                new OpenLayers.Rule({
                    symbolizer: temp_symbolizer_style
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
                }
            })
        ]
    }),
    "select": new OpenLayers.Style(selected_prop_style),
    "temporary": new OpenLayers.Style(null, {
        rules: [
            new OpenLayers.Rule({
                symbolizer: temp_symbolizer_style
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
                    }
                })
            ]
        }),
        "select": new OpenLayers.Style(selected_stand_style),
        "temporary": new OpenLayers.Style(null, {
            rules: [
                new OpenLayers.Rule({
                    symbolizer: temp_symbolizer_style
                })
            ]
        })
    }),

standProperty:
    new OpenLayers.StyleMap(property_style),
    
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
        "select": selected_stand_style
    }),
    
strataSelect: selected_stand_style,
    
strataShiftSelect: selected_stand_style

};

