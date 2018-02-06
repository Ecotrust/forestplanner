var cashChart1;
var cashChart2;
var cashChartYAxisRange = {};

var cashChartOptions = {
    stackSeries: true,
    seriesColors:['#8DD3C7', '#FFFFB3', '#BEBADA'],
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
        numberRows: 1
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

var refreshCashflow = function() {
  var opt1 = $('#cash-select-scenario1').find(":selected").val();
  if (!opt1) {
    $('#cash-chart1').html('<p class="muted" style="margin: 25px; font-size: 16pt;"> Select a scenario to evaluate. </p>');
    return false;
  }
  var cashflow_url1 = "/features/scenario/links/scenario-cash-flow/trees_scenario_" + opt1 +"/";

  $('#cash-chart1').html('');
  if (cashChart1) {
    cashChart1.destroy();
  }
  $('#loading-cash-chart1').show();

  var xhr1 = $.ajax( cashflow_url1, {
    dataType: 'json'
  }).done(function(data) {
    if (data && data['years']) {
      var date = new Date();
      for (var i = 0; i < data['years'].length; i++) {
        data['years'][i] = date.getFullYear() + (i * 5);
      }
      cashChartOptions.axes.xaxis.ticks = data['years'];
      var dataSeries = [
         data['haul'],
         data['cable'],
         data['ground'],
      ];
      cashChart1 = $.jqplot('cash-chart1', dataSeries, cashChartOptions);
    } else {
      $('#cash-chart1').html('');
    }
    $('#loading-cash-chart1').hide();
  });
};

$(document).ready(function() {
    $("#scenario-cash-tab").on('shown', function() {refreshCashflow();});
    $("#cash-select-scenario1").change(function() {refreshCashflow();});
});
