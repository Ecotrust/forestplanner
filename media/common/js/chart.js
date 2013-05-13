var globalChartOptions = {
      seriesColors: chartColors,
      grid: {
          backgroundColor: "white"
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

var chartColors = [ "#4bb2c5", "#c5b47f", "#EAA228", 
                    "#579575", "#839557", "#958c12",
                    "#953579", "#4b5de4", "#d8b83f", 
                    "#ff5800", "#0085cc"];  // assumes max of 11 series will be shown

var scenarioPlot; 

var chartMetrics = {
  'carbon': {
    'variableName': 'carbon',
    'title': "Carbon Sequestration",
    'axisLabel': "Carbon (tons)",
    'axisFormat': '%d'
  },
  'timber': {
    'variableName': 'timber',
    'title': "Timber Harvested",
    'axisLabel': "Harvest (mbdft)",
    'axisFormat': '%d'
  }
}

var refreshCharts = function(){

  var selectedMetric = $("#chart-metrics-select").find(":selected").val();
  if (!selectedMetric || !selectedMetric in chartMetrics) {
      alert("WARNING: no metric selected. Defaulting to 'carbon'");
      selectedMetric = 'carbon';
  }

  // destroy then replot to prevent memory leaks
  if (scenarioPlot) {
    $('#chart-scenario *').unbind(); // iexplorer
    scenarioPlot.destroy();
  }

  var containerWidth = $("#scenario-charts-tab-content").width();
  $("#chart-scenario").width(containerWidth - 150);

  var scenarioData = [];
  var scenarioLabels = [];
  var metric = chartMetrics[selectedMetric];

  $.each(app.scenarios.viewModel.selectedFeatures(), function() {
    var newData;
    var resall;
    var res = this.fields.output_scheduler_results;
    
    if (res) {
        resall = res['__all__'];
    }

    if (resall) {
        newData = resall[metric.variableName];
    } else {
        newData = [[null]];
    }

    scenarioData.push(newData); 
    scenarioLabels.push({'label': this.fields.name}); 

  });

  if (scenarioData.length > 0) {
    scenarioPlot = $.jqplot('chart-scenario', scenarioData, $.extend(globalChartOptions, {
        title: metric.title,
        series: scenarioLabels, 
        axes: {
            xaxis: {
              label: "Year",
              renderer: $.jqplot.DateAxisRenderer,
              tickOptions: {formatString:'%Y'},
              min:'Jan 01, 2000 8:00AM', 
              tickInterval:'10 years',
              pad: 0
            },
            yaxis: {
              label: metric.axisLabel,
              tickOptions: {formatString: metric.axisFormat}
            }
        }
    }));
  }

  $("tr.scenario-row").click( function() {
      var row = $(this);
      row.find("div.scenario-details").fadeToggle();
  });
};
