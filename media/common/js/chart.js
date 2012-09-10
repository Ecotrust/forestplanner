var timberPlot, carbonPlot; 

var chartColors = [ "#4bb2c5", "#c5b47f", "#EAA228", 
                    "#579575", "#839557", "#958c12",
                    "#953579", "#4b5de4", "#d8b83f", 
                    "#ff5800", "#0085cc"];  // assumes max of 11 series will be shown

var globalChartOptions = {
      seriesColors: chartColors,
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

  var carbonData = [];
  var timberData = [];
  var carbonLabels = [];
  var timberLabels = [];

  $.each(app.scenarios.viewModel.selectedFeatures(), function() {
    var newTimberData;
    var newCarbonData;

    var res = JSON.parse(this.fields.output_scheduler_results);
    var resall = res['__all__'];

    if (resall) {
        newTimberData = resall.timber; 
        newCarbonData = resall.carbon; 
    }

    if (newTimberData) {
        timberData.push(newTimberData); 
        timberLabels.push({'label': this.fields.name}); 
    }

    if (newCarbonData) {
        carbonData.push(newCarbonData); 
        carbonLabels.push({'label': this.fields.name}); 
    }

  });

  if (carbonData.length > 0) {
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
  }

  if (timberData.length > 0) {
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
  }
};
