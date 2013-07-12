var cashChart1;
var cashChart2;

var cashChartOptions = {
    stackSeries: true,
    seriesColors:['#D95F0E', '#EF3B2C','#415DAB', '#CB181D', '#FB6A4A', '#000000'],
    seriesDefaults:{
      renderer:$.jqplot.BarRenderer,
      useNegativeColors: false,
      rendererOptions: {
        fillToZero: true,
        highlightMouseOver: false,
        varyBarColor: true
      }
    },
    series:[
      {label:'Transportation Costs '},
      {label:'Cable Harvest Costs '},
      {label:'Timber Sale Income '},
      {label:'Ground Harvest Costs '},
      {label:'Helicopter Harvest Costs '},
      {
        label:'Net Revenue ',
        renderer:$.jqplot.LineRenderer,
        disableStack: true
      }
    ],
    highlighter : {
      show : true,
      showMarker: false,
      tooltip: true,
      useAxesFormatters: true,
      tooltipAxes: 'y',
      bringSeriesToFront: false
    },
    axes: {
      xaxis: {
        renderer: $.jqplot.CategoryAxisRenderer
        //ticks: data['years']
      },
      yaxis: {
        autoscale:true,
        tickOptions: {formatString: "$%'d"}
      }
    },
    legend: {
      renderer: $.jqplot.EnhancedLegendRenderer,
      rendererOptions: {
        // numberRows: 2
        numberColumns: 3
      },
      show: true,
      location: 'n',
      placement: 'outside'
    }
};

var refreshCashflow = function() {

  var opt1 = $('#cash-select-scenario1').find(":selected").val();
  var cashflow_url1 = "/features/generic-links/links/geojson/trees_scenario_" + opt1 +"/";

  var opt2 = $('#cash-select-scenario2').find(":selected").val();
  var cashflow_url2 = "/features/generic-links/links/geojson/trees_scenario_" + opt2 +"/";

  console.log(cashflow_url1);
  console.log(cashflow_url2);

  // $.get( cashflow_url2, function(data) {
  //     if (data.features.length) {
  //         standScenario2.addFeatures(app.geojson_format.read(data));
  //         timemapScenarioData[opt2] = data;
  //         processBreaks();
  //         standScenario1.redraw();
  //         standScenario2.redraw();
  //     } else {
  //         console.log("First scenario doesn't have any features! Check scenariostands...");
  //         $("#error-timemap2").fadeIn();
  //     }
  // });

  var data = {
    'heli':
        [-0.0, -0.0, -0.0, -0.0, -49157.0, -21592.0, -107744.0, -12981.0,
         -10320.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -15980.0, -0.0, -0.0,
         -0.0, -0.0],
    'cable':
        [-0.0, -141242.0, -152875.0, -0.0, -0.0, -0.0, -0.0, -64290.0,
         -141968.0, -19882.0, -149182.0, -136889.0, -151957.0, -14663.0,
         -80961.0, -52539.0, -85341.0, -12559.0, -62926.0, -65398.0],
    'ground':
        [-0.0, -0.0, -0.0, -0.0, -1533.0, -0.0, -0.0, -7990.0, -1525.0,
         -0.0, -0.0, -17670.0, -1132.0, -0.0, -0.0, -8501.0, -955.0, -0.0,
         -0.0, -5316.0],
    'haul':
        [-0.0, -2064.0, -1032.0, -0.0, -5516.0, -2321.0, -11268.0, -10506.0,
         -17159.0, -2579.0, -23051.0, -
         24713.0, -23026.0, -2149.0, -12731.0,
         -12399.0, -13712.0, -1891.0, -10322.0, -9817.0],
    'years':
        [2013, 2018, 2023, 2028, 2033, 2038, 2043, 2048, 2053, 2058, 2063,
         2068, 2073, 2078, 2083, 2088, 2093, 2098, 2103, 2108],
    'gross':
        [0.0, 151119.00135682218, 202940.31882041722, 0.0,
         73958.71780213497, 26617.055625375597, 134400.7016302686,
         128100.24518252583, 155266.69377153495, 28143.253466692706,
         225108.01569275412, 199372.21764986034, 153572.74052135315,
         17245.574336887723, 102382.06551396813, 109212.064463478,
         104798.66954346969, 16743.37352151583, 87347.72519781529,
         80698.11790092077],
    'net':
        [0.0, 7813.001356822177, 49033.31882041722, 0.0, 17752.71780213497,
         2704.0556253755967, 15388.701630268595, 32333.245182525832,
         -15705.306228465051, 5682.253466692706, 52875.015692754125,
         20100.217649860337, -22542.259478646854, 433.5743368877229,
         8690.065513968133, 19793.064463478004, 4790.6695434696885,
         2293.3735215158304, 14099.725197815293, 167.1179009207699]
  };

  cashChartOptions.axes.xaxis.ticks = data['years'];

  var dataSeries = [
     data['haul'],
     data['cable'],
     data['gross'],
     data['ground'],
     data['heli'],
     data['net']
  ];

  cashChart1 = $.jqplot('cash-chart1', dataSeries,
    cashChartOptions
  );

  cashChart2 = $.jqplot('cash-chart2', dataSeries,
    $.extend({}, cashChartOptions, {legend: {show: false}})
  );

};

$(document).ready(function() {

    $("#scenario-cash-tab").on('shown', function() {refreshCashflow();});
    // $("#cash-select-scenario1").change(function() {refreshTimeMap(true, true);});
    // $("#cash-select-scenario2").change(function() {refreshTimeMap(true, true);});

    var timemapInitialized = false;

});
