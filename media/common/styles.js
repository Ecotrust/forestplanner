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
                        strokeColor: "#444444",
                    },
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
                        fillColor: "#44ff00",
                    },
                    "Polygon": {
                        pointRadius: 5,
                        fillColor: "white",
                        fillOpacity: 0.35,
                        strokeWidth: 2,
                        strokeOpacity: 1,
                        strokeColor: "#44ff00"
                    },
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
                        strokeColor: "#444444",
                        label: "${name}",
                        labelAlign: "cc",
                        fontColor: "#333333",
                        fontOpacity: 0.9,
                        fontFamily: "Arial",
                        fontSize: 14
                    },
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
                        fillColor: "#44ff00",
                    },
                    "Polygon": {
                        pointRadius: 5,
                        fillColor: "white",
                        fillOpacity: 0.35,
                        strokeWidth: 2,
                        strokeOpacity: 1,
                        strokeColor: "#44ff00"
                    },
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
                    },
                }
            })
        ]
    }),
    "select": new OpenLayers.Style({
        graphicZIndex: 10000,
        strokeWidth: 2,
        strokeOpacity: 1,
        strokeColor: "#44ff00"
    }),
    "temporary": new OpenLayers.Style(null, {
        rules: [
            new OpenLayers.Rule({
                symbolizer: {
                    "Point": {
                        pointRadius: 5,
                        fillColor: "#44ff00",
                    },
                    "Polygon": {
                        pointRadius: 5,
                        fillColor: "white",
                        fillOpacity: 0.35,
                        strokeWidth: 2,
                        strokeOpacity: 1,
                        strokeColor: "#44ff00"
                    },
                }
            })
        ]
    })
})
};

console.log(map_styles);
