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
          rendererOptions: { smooth: false }
      },
      highlighter: {
          show: true,
          sizeAdjust: 7.5
      },
      legend: {
          renderer: $.jqplot.EnhancedLegendRenderer,
          show: true,
          showLabels: true,
          location: 'n',
          placement: 'inside',
          //marginTop: "60px",
          //marginBottom: "-25px",
          fontSize: '11px',
          fontFamily: ["Lucida Grande","Lucida Sans Unicode","Arial","Verdana","sans-serif"],
          rendererOptions: {
              seriesToggle: 'normal',
              numberRows: 1
          }
      }
};

var chartColors = [ "#4bb2c5", "#c5b47f", "#EAA228",
                    "#579575", "#839557", "#958c12",
                    "#953579", "#4b5de4", "#d8b83f",
                    "#ff5800", "#0085cc"];  // assumes max of 11 series will be shown

var scenarioPlot;

var chartMetrics = {
  'agl_carbon': {
    'variableName': 'agl_carbon',
    'title': "Carbon (Live Tree)",
    'axisLabel': "Carbon (metric tons C)",
    'axisFormat': "%'d"
  },
  'total_carbon': {
    'variableName': 'total_carbon',
    'title': "Carbon (Stand Total)",
	'axisLabel': "Carbon (metric tons C)",
    'axisFormat': "%'d"
  },
  'harvested_timber': {
    'variableName': 'harvested_timber',
    'title': "Harvest (per period)",
	'axisLabel': "Timber yield (MBF)",
    'axisFormat': "%'d"
  },
  'cum_harvest': {
    'variableName': 'cum_harvest',
    'title': "Harvest (cumulative)",
    'axisLabel': "Timber yield (MBF)",
    'axisFormat': "%'d"
  },
  'age': {
    'variableName': 'age',
    'title': "Age",
    'axisLabel': "Age (years)",
    'axisFormat': "%'d"
  },
  'ba': {
    'variableName': 'ba',
    'title': "Basal Area",
    'axisLabel': "Basal Area (ft2/acre)",
    'axisFormat': "%'d"
  },
  'tpa': {
    'variableName': 'tpa',
    'title': "Trees per acre",
    'axisLabel': "Trees per acre",
    'axisFormat': "%'d"
  },
  'standing_vol': {
    'variableName': 'standing_vol',
    'title': "Standing Volume",
    'axisLabel': "Standing volume (ft3)",
    'axisFormat': "%'d"
  },
  'standing_timber': {
    'variableName': 'standing_timber',
    'title': "Standing Boardfeet",
    'axisLabel': "Standing Boardfeet (MBF)",
    'axisFormat': "%'d"
  },
  'fire': {
    'variableName': 'fire',
    'title': "Fire Hazard",
    'axisLabel': "High Fire Hazard",
    'axisFormat': "%'d"
  },
  'pp_btl': {
    'variableName': 'pp_btl',
    'title': "Mountain Pine Beetle Hazard to PP",
    'axisLabel': "High Pine Beetle Hazard to PP",
    'axisFormat': "%'d"
  },
  'lp_btl': {
    'variableName': 'lp_btl',
    'title': "Mountain Pine Beetle Hazard to LP",
    'axisLabel': "High Pine Beetle Hazard to LP",
    'axisFormat': "%'d"
  },
  'es_btl': {
    'variableName': 'lp_btl',
    'title': "Spruce Beetle Hazard",
    'axisLabel': "High Spruce Beetle Hazard",
    'axisFormat': "%'d"
  }
};

var refreshCharts = function(){

  var selectedMetric = $("#chart-metrics-select").find(":selected").val();
  if (!selectedMetric || !(selectedMetric in chartMetrics)) {
      alert("WARNING: no metric selected. Defaulting to 'agl_carbon'");
      selectedMetric = 'agl_carbon';
  }

  // destroy then replot to prevent memory leaks
  if (scenarioPlot) {
    $('#chart-scenario *').unbind(); // iexplorer
    scenarioPlot.destroy();
  }

  var containerWidth = $("#scenario-charts-tab-content").width();
  var containerHeight = $(window).height();
  $("#chart-scenario").width(containerWidth - 30);
  $("#chart-scenario").height(containerHeight - 300);

  var scenarioData = [];
  var scenarioLabels = [];
  var metric = chartMetrics[selectedMetric];

  $.each(app.scenarios.viewModel.selectedFeatures(), function() {
    var newData = [];
    var resall;
    var res = this.fields.output_property_metrics;

    if (res) {
        resall = res['__all__'];
    }

    if (resall) {
        newData = resall[metric.variableName];
    }

    if (newData.length === 0) {
        newData = [[null]];
    }

    scenarioData.push(newData);
    scenarioLabels.push({'label': this.fields.name});

  });

  /*
   *  AGL Regional baseline, hardcoded madness here
   */
  if (metric.variableName == "agl_carbon") {
    var acres = app.scenarios.viewModel.property.acres();
    var baseline_peracre;
    switch (app.scenarios.viewModel.property.variant()) {
      case "Pacific Northwest Coast":
          baseline_peracre = 38.6; // units = metric tons of carbon per acre (not CO2)
          break;
      case "South Central Oregon":
          baseline_peracre = 13.2;
          break;
      case "Eastside Cascades":
          baseline_peracre = 13.2;
          break;
      case "Inland California and Southern Cascades":
          baseline_peracre = 23.6;
          break;
      case "Westside Cascades":
          baseline_peracre = 32.1;
          break;
      case "Blue Mountains":
          baseline_peracre = 10.4;
          break;
    }
    if (baseline_peracre) {
        // baseline = AGL (tC/acre) * acres = AGL(metric tons C)
        var baseline = baseline_peracre * acres;
        scenarioData.push([['2001-12-31 11:59PM', baseline], ['2120-12-31 11:59PM', baseline]]);
        scenarioLabels.push({'label': "Regional Average (" + baseline_peracre + " tC/ac)"});
    }
  }

  if (scenarioData.length > 0) {
    scenarioPlot = $.jqplot('chart-scenario', scenarioData, $.extend(globalChartOptions, {
        //title: metric.title,
        series: scenarioLabels,
        axes: {
            xaxis: {
              label: "Year",
              renderer: $.jqplot.DateAxisRenderer,
              tickOptions: {formatString:'%Y'},
              min:'Jan 01, 2010 8:00AM',
              max:'Jan 01, 2111 8:00AM',
              tickInterval:'10 years',
              pad: 0
            },
            yaxis: {
              label: metric.axisLabel,
              tickInterval: 10000,
              tickOptions: {formatString: metric.axisFormat}
            }
        }
    }));
  }
};
