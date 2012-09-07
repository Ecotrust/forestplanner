var timberPlot, carbonPlot; 

var carbonData = [];
var timberData = [];

var scenario1 = { 
    "type": "FeatureCollection",
    "id": "trees_scenario_1",
    "name": "trees_scenario_1",
    "features": [
        { 
            "type": "Feature",
            "geometry": null,
            "properties": {
                "id": "__all__",
                "carbon": [
                    ['2004-08-12 4:00PM',3.2], 
                    ['2024-09-12 4:00PM',5.7], 
                    ['2048-10-12 4:00PM',6.5], 
                    ['2067-12-12 4:00PM',4.0],
                ],
                "timber": [
                    ['2004-08-12 4:00PM',4], 
                    ['2024-09-12 4:00PM',6.5], 
                    ['2048-10-12 4:00PM',5.7], 
                    ['2067-12-12 4:00PM',3.2],
                ]
            }
        },
        { 
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0]
                ]
            },
            "properties": {
                "id": "trees_stand_123",
                "carbon": [
                    ['2004-08-12 4:00PM',4], 
                    ['2024-09-12 4:00PM',6.5], 
                    ['2048-10-12 4:00PM',5.7], 
                    ['2067-12-12 4:00PM',3.2],
                ],
                "timber": [
                    ['2004-08-12 4:00PM',3.2], 
                    ['2024-09-12 4:00PM',5.7], 
                    ['2048-10-12 4:00PM',6.5], 
                    ['2067-12-12 4:00PM',4.0],
                ]
            }
        }
    ]
}

var scenario2 = { 
    "type": "FeatureCollection",
    "id": "trees_scenario_2",
    "name": "trees_scenario_2",
    "features": [
        { 
            "type": "Feature",
            "geometry": null,
            "properties": {
                "id": "__all__",
                "carbon": [
                    ['2004-08-12 4:00PM',4], 
                    ['2024-09-12 4:00PM',6.5], 
                    ['2048-10-12 4:00PM',5.7], 
                    ['2067-12-12 4:00PM',3.2],
                ],
                "timber": [
                    ['2004-08-12 4:00PM',3.2], 
                    ['2024-09-12 4:00PM',5.7], 
                    ['2048-10-12 4:00PM',6.5], 
                    ['2067-12-12 4:00PM',4.0],
                ]
            }
        },
        { 
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [102.0, 0.0], [103.0, 1.0], [104.0, 0.0], [105.0, 1.0]
                ]
            },
            "properties": {
                "id": "trees_stand_123",
                "carbon": [
                    ['2004-08-12 4:00PM',4], 
                    ['2024-09-12 4:00PM',6.5], 
                    ['2048-10-12 4:00PM',5.7], 
                    ['2067-12-12 4:00PM',3.2],
                ],
                "timber": [
                    ['2004-08-12 4:00PM',3.2], 
                    ['2024-09-12 4:00PM',5.7], 
                    ['2048-10-12 4:00PM',6.5], 
                    ['2067-12-12 4:00PM',4.0],
                ]
            }
        }
    ]
}

var scenario3 = { 
    "type": "FeatureCollection",
    "id": "trees_scenario_3",
    "name": "trees_scenario_3",
    "features": [
        { 
            "type": "Feature",
            "geometry": null,
            "properties": {
                // we should have an id == '__all__' as the first feature
                "id": "__BAD_MISSING_ALL__", 
                "carbon": [
                    ['2004-08-12 4:00PM',2], 
                    ['2024-09-12 4:00PM',3.5], 
                    ['2048-10-12 4:00PM',3.7], 
                    ['2067-12-12 4:00PM',1.2],
                ],
                "timber": [
                    ['2004-08-12 4:00PM',2.2], 
                    ['2024-09-12 4:00PM',4.7], 
                    ['2048-10-12 4:00PM',3.5], 
                    ['2067-12-12 4:00PM',1.0],
                ]
            }
        }
    ]
}

var scenario4 = { 
    "type": "FeatureCollection",
    "id": "trees_scenario_4",
    "name": "trees_scenario_4",
    "features": [
        { 
            "type": "Feature",
            "geometry": null,
            "properties": {
                "id": "__all__",
                // missing carbon
                "timber": [
                    ['2004-08-12 4:00PM',2.2], 
                    ['2024-09-12 4:00PM',4.7], 
                    ['2048-10-12 4:00PM',3.5], 
                    ['2067-12-12 4:00PM',1.0],
                ]
            }
        }
    ]
}

var scenarios = [scenario1, scenario2, scenario3, scenario4];
var carbonLabels = [];
var timberLabels = [];

$.each(scenarios, function() {
    var newTimberData;
    var newCarbonData;

    $.each(this.features, function() { 
        if(this.properties.id==='__all__') { 
            newTimberData = this.properties.timber; 
            newCarbonData = this.properties.carbon; 
            return false; // exit 
        }  
    });

    if (newTimberData) {
        timberData.push(newTimberData); 
        timberLabels.push({'label': this.name}); 
    }

    if (newCarbonData) {
        carbonData.push(newCarbonData); 
        carbonLabels.push({'label': this.name}); 
    }
});

var globalChartOptions = {
      grid: {
          backgroundColor: "white",
      },
      axesDefaults: {
          labelRenderer: $.jqplot.CanvasAxisLabelRenderer
      },
      seriesDefaults: { // applies to all rows
          lineWidth: 2,
          style: 'square',
          rendererOptions: { smooth: true }
      },
      highlighter: {
          show: true,
          sizeAdjust: 7.5
      },
      legend: {
          renderer: $.jqplot.EnhancedLegendRenderer,
          show: true,
          showLabels: true,
          location: 'ne',
          placement: 'outside',
          fontSize: '11px',
          fontFamily: ["Lucida Grande","Lucida Sans Unicode","Arial","Verdana","sans-serif"],
          rendererOptions: {
              seriesToggle: 'normal'
          }
      }
};

var refreshCharts = function(){

  // destroy then replot to prevent memory leaks
  if (carbonPlot) {
    $('chart-carbon *').unbind(); // iexplorer
    carbonPlot.destroy();
  }

  if (timberPlot) {
    $('chart-timber *').unbind(); // iexplorer
    timberPlot.destroy();
  }

  carbonPlot = $.jqplot('chart-carbon', carbonData, $.extend(globalChartOptions, {
      title: 'Carbon Sequestration over time',
      series: carbonLabels, 
      axes: {
        xaxis: {
          label: "Time",
          renderer: $.jqplot.DateAxisRenderer,
          tickOptions: {formatString:'%Y'},
          min:'Jan 01, 2000 8:00AM', 
          tickInterval:'10 years',
          pad: 0
        },
        yaxis: {
          label: "Carbon",
          tickOptions: {formatString:'%.1f tons'}
        }
      }
  }));

  timberPlot = $.jqplot('chart-timber', timberData, $.extend(globalChartOptions, {
      title: 'Timber Harvest over time',
      series: timberLabels, 
      axes: {
        xaxis: {
          label: "Time",
          renderer: $.jqplot.DateAxisRenderer,
          tickOptions: {formatString:'%Y'},
          min:'Jan 01, 2000 8:00AM', 
          tickInterval:'10 years',
          pad: 0
        },
        yaxis: {
          label: "Timber",
          tickOptions: {formatString:'%.1f bdft'}
        }
      }
  }));
};
