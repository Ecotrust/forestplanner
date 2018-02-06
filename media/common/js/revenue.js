var revenueChart1;
var revenueChart2;
var revenueChartYAxisRange = {};

var revenueChartOptions = {
    stackSeries: true,
    seriesColors:['#D3C78D'],
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
      {label:'Estimated Gross Timber Revenue '},
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

var refreshRevenue = function() {
  var opt1 = $('#revenue-select-scenario1').find(":selected").val();
  if (!opt1) {
    $('#revenue-chart1').html('<p class="muted" style="margin: 25px; font-size: 16pt;"> Select a scenario to evaluate. </p>');
    return false;
  }
  var revenue_url1 = "/features/scenario/links/scenario-revenue/trees_scenario_" + opt1 +"/";

  $('#revenue-chart1').html('');
  if (revenueChart1) {
    revenueChart1.destroy();
  }
  $('#loading-revenue-chart1').show();

  var xhr1 = $.ajax( revenue_url1, {
    dataType: 'json'
  }).done(function(data) {
    if (data && data['years']) {
      var date = new Date();
      for(var i = 0; i < data['years'].length; i++) {
          data['years'][i] = date.getFullYear() + (i * 5);
      }
      revenueChartOptions.axes.xaxis.ticks = data['years'];
      var dataSeries = [
         data['gross'],
      ];
      revenueChart1 = $.jqplot('revenue-chart1', dataSeries, revenueChartOptions);
    } else {
      $('#revenue-chart1').html('');
    }
    $('#loading-revenue-chart1').hide();
  });
};

$(document).ready(function() {
    $("#scenario-revenue-tab").on('shown', function() {refreshRevenue();});
    $("#revenue-select-scenario1").change(function() {refreshRevenue();});
});
