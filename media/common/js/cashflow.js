var cashChart1;
var cashChart2;
var cashChartYAxisRange = {};

var cashChartOptions = {
    stackSeries: true,
    //seriesColors:['#D95F0E', '#EF3B2C', '#CB181D', '#D95F0E','#415DAB', '#EF3B2C','#AB5D41', '#FB6A4A', '#000000'],
    seriesColors:['#8DD3C7', '#FFFFB3', '#BEBADA', '#FB8072'],
    seriesDefaults:{
      renderer:$.jqplot.BarRenderer,
      useNegativeColors: false,
      rendererOptions: {
        fillToZero: true,
        highlightMouseOver: false,
        varyBarColor: true,
        forceTickAt0: true
      }
    },
    series:[
      {label:'Transportation '},
      {label:'Cable Harvest'},
      {label:'Ground Harvest '},
      {label:'Helicopter Harvest '}
      // {label:'Timber Revenue '},
      // {label:'Administration '},
      // {label:'Taxes '},
      // {label:'Road Maintenance '},
      // {
      //   label:'Net (Cumulative, Discounted)',
      //   renderer:$.jqplot.LineRenderer,
      //   rendererOptions: {forceTickAt0: true},
      //   disableStack: true
      // }
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
        numberRows: 2
        //numberColumns: 4
      },
      show: true,
      location: 'n',
      placement: 'outside'
    }
};


function sigFigs(n, sig) {
    var mult = Math.pow(10, sig - Math.floor(Math.log(n) / Math.LN10) - 1);
    return Math.round(n * mult) / mult;
}

var refreshCashflow = function(refresh1, refresh2) {
  var opt1 = $('#cash-select-scenario1').find(":selected").val();
  var opt2 = $('#cash-select-scenario2').find(":selected").val();

  var cashflow_url1 = "/features/scenario/links/scenario-cash-flow/trees_scenario_" + opt1 +"/";
  var cashflow_url2 = "/features/scenario/links/scenario-cash-flow/trees_scenario_" + opt2 +"/";

  $('#cash-chart1').html('');
  $('#cash-chart2').html('');
  if (cashChart1) {
    cashChart1.destroy();
  }
  if (cashChart2) {
    cashChart2.destroy();
  }

  if (!opt1) {
    return false;
  }

  $('#loading-cash-chart1').show();
  $('#loading-cash-chart2').show();

  var xhr1 = $.ajax( cashflow_url1, {
    dataType: 'json'
  });
  var xhr2 = $.ajax( cashflow_url2, {
    dataType: 'json'
  });


  $.when(xhr1, xhr2).done(function(r1, r2) {
    var data = r1[0];
    if (data && data['years']) {
      cashChartOptions.axes.xaxis.ticks = data['years'];
      var dataSeries = [
         data['haul'],
         data['cable'],
         data['ground'],
         data['heli']
         // data['gross'],
         // data['admin'],
         // data['tax'],
         // data['road'],
         // data['cum_disc_net']
      ];
      cashChart1 = $.jqplot('cash-chart1', dataSeries, cashChartOptions);
    } else {
      $("#cash1").hide();
      $('#cash-chart1').html('');
    }
    $('#loading-cash-chart1').hide();

    if (opt1 !== opt2) {
      data = r2[0];
      if (data && data['years']) {
        cashChartOptions.axes.xaxis.ticks = data['years'];
        var dataSeries = [
           data['haul'],
           data['cable'],
           data['ground'],
           data['heli']
           // data['gross'],
           // data['admin'],
           // data['tax'],
           // data['road'],
           // data['cum_disc_net']
        ];
        cashChart2 = $.jqplot('cash-chart2', dataSeries, cashChartOptions);
      }
      $('#loading-cash-chart2').hide();
    } else {
      $('#loading-cash-chart2').hide();
      $("#cash2").hide();
      $('#cash-chart2').html('');
      cashChart2 = null;
    }

    if (cashChart2) {
      $("#cash2").show();

      // sync the axes
      var newMin = Math.min(cashChart1.axes.yaxis.min, cashChart2.axes.yaxis.min);
      var newMax = Math.max(cashChart1.axes.yaxis.max, cashChart2.axes.yaxis.max);

      newYAxis = {
        'min': newMin,
        'max': newMax,
        // Looks wierd but ensures tick line at zero
        'ticks': [newMin, 0, newMax]
        // 'ticks': [newMin, -1*sigFigs(-1*newMin/2, 2), 0, sigFigs(newMax/2, 2), newMax]
      };

      cashChart1.resetAxesScale();
      $.extend(cashChart1.axes.yaxis, newYAxis);
      cashChart1.replot();

      cashChart2.resetAxesScale();
      $.extend(cashChart2.axes.yaxis, newYAxis);
      cashChart2.replot();
    }

  });
};

$(document).ready(function() {
    $("#scenario-cash-tab").on('shown', function() {refreshCashflow(true, true);});
    $("#cash-select-scenario1").change(function() {refreshCashflow(true, false);});
    $("#cash-select-scenario2").change(function() {refreshCashflow(false, true);});
});
