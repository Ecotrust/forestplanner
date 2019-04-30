scenarios = {};
for (var i = 0; i < scenario_list.length; i++) {
  scenario = scenario_list[i];
  scenarios[scenario.pk] = scenario.fields;
}

var margin = {top: 20, right: 20, bottom: 50, left: 55},
      width = window.innerWidth/3 - margin.left - margin.right, // Use the window's width
      height = window.innerHeight/3 - margin.top - margin.bottom; // Use the window's height

// TODO: Have admin select color for each scenario
var chartColors = [ "#4bb2c5", "#c5b47f", "#EAA228",
                    "#579575", "#839557", "#958c12",
                    "#953579", "#4b5de4", "#d8b83f",
                    "#ff5800", "#0085cc"];  // assumes max of 11 series will be shown

// Define the div for the tooltip
var tooltipDiv = d3.select("body")
  .append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

formatTick = function(val, max_char) {
  var val_len = parseFloat(val.toPrecision(max_char)).toString().length;
  if ( val_len > max_char) {
    if (val_len > max_char + 3) {
      if (val_len > max_char + 6) {
        if (val_len > max_char + 9) {
          new_val = val.toPrecision(max_char-2);
        } else {
          new_val = parseFloat((val/1000000000).toPrecision(3)) + "B";
        }
      } else {
        new_val = parseFloat((val/1000000).toPrecision(3)) + "M";
      }
    } else {
      new_val = parseFloat((val/1000).toPrecision(3)) + "K";
    }
  } else {
    new_val = parseFloat(val.toPrecision(max_char));
  }
  return new_val;
}


loadGraphs = function() {
  if ($('input:checked').length > 0) {
    $('#accordion-metrics').show();
    $('#no-metrics-message').hide();
    // For each topic
    $.each(metric_list, function(topic_index, topic){
      // For each metric graph
      $.each(topic.metrics, function(metric_index, metric){   // ---------------METRIC--------------------
        metric_data = {};

        var metric_key = metric.metric_key;

        if (metric.hasOwnProperty('axes')) {
          xlabel = metric.axes.x.label;
          ylabel = metric.axes.y.label;
        } else {
          xlabel = 'X-Axis';
          ylabel = 'Y-Axis';
        }

        // Create SVG Element
        var svg = d3.select("#" + metric.id)
          .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
          .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var xdomain = [];
        var yvalues = [];
        // For each scenario
        $.each($("input:checked"), function(index, scenario_item){     // ---------------SCENARIO--------------------
          // Get scenario data
          scenario = scenarios[scenario_item.value];
          if (scenario.output_property_metrics != null){
            var raw_data = scenario.output_property_metrics.__all__[metric_key];
          } else {
            raw_data = []
            if (metric_index == 0 && topic_index==0) {
              alert('Data for ' + scenario.name + ' are not ready yet. Please try refreshing the page in a few minutes.');
            }
          }
          metric_data[scenario.name] = [];
          // Loop through nodes:
          $.each(raw_data, function(data_index, datum){         // ---------------DATUM--------------------
            if (datum[1] != null) {
              // This assumes all x values are a timestamp like YYYY-12-31 11:59PM
              var year = datum[0].split('-12-31 11:59PM')[0];
              if (xdomain.indexOf(year) < 0) {
                xdomain.push(year);
              }
              metric_data[scenario.name].push({'x': year, 'y':datum[1]});
              yvalues.push(datum[1]);
            }
          })                                                  // ---------------END DATUM--------------------
        });                                               // ---------------END SCENARIO--------------------
        xdomain.sort(function(a, b){ return parseFloat(a)-parseFloat(b);});
        yvalues.sort(function(a, b){ return parseFloat(a)-parseFloat(b);});
        // Create X axis measures
        var xScale = d3.scaleLinear()
          .domain([xdomain[0], xdomain[xdomain.length-1]]) // input
          .range([0, width]); // output

        // Create Y axis measures
        var yScale = d3.scaleLinear()
          // .domain([ymin, ymax]) // input
          .domain([yvalues[0], yvalues[yvalues.length-1]]) // input
          .range([height, 0]); // output

        // create line generator
        line_generator = d3.line()
          .x(function(d) { return xScale(d.x); }) // set the x values for the line generator
          .y(function(d) { return yScale(d.y); }) // set the y values for the line generator
          // .interpolate("linear");
          // .curve(d3.curveMonotoneX) // apply smoothing to the line

        // Append axis measures:
        svg.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + height + ")")
          .call(d3.axisBottom(xScale)
                .ticks(10)
                .tickFormat(d3.format("d"))) // Create an axis component with d3.axisBottom
          .append('text') // x-axis Label
            .attr('class','label')
            .attr('x',150)
            .attr('y',25)
            .attr('dy','.71em')
            .style('text-anchor','start')
            .style('fill','black')
            .html(xlabel);

        svg.append("g")
            .attr("class", "y axis")
            .call(d3.axisLeft(yScale)
              .tickFormat(function(d){ return formatTick(d, 4)})) // Create an axis component with d3.axisLeft
          .append('text') // y-axis Label
            .attr('class','label')
            .attr('transform','rotate(-90)')
            .attr('x',-30)
            .attr('y',-48)
            .attr('dy','.71em')
            .style('text-anchor','end')
            .style('fill','black')
            .html(ylabel);

        var legend = svg.append("g")
          .attr("class", "legend")
          .attr("height", 120)
          .attr("width", width)

        $.each(Object.keys(metric_data), function(draw_index, scenario_key){    // ---------------SCENARIO AGAIN--------------------
          // Append the path, bind the data, and call the line generator
          svg.append("path")
            .datum(metric_data[scenario_key]) // 10. Binds data to the line
            .attr("class", "line") // Assign a class for styling
            .style('stroke', chartColors[draw_index])
            .attr("d", line_generator); // 11. Calls the line generator

          // Appends a circle for each datapoint

          svg.selectAll("dot")
            .data(metric_data[scenario_key])
            .enter().append("circle") // Uses the enter().append() method
            .attr("class", "dot") // Assign a class for styling
            .style('fill', chartColors[draw_index])
            .attr("cx", function(d) { return xScale(d.x) })
            .attr("cy", function(d) { return yScale(d.y) })
            .attr("r", 5)
            .on("mouseover", function(d) {
              tooltipDiv.transition()
                .duration(200)
                .style('opacity', .8);
              tooltipDiv.html(d.x + ', ' + formatTick(d.y, 4))
                .style("left", (d3.event.pageX) + "px")
                .style("top", (d3.event.pageY - 28) + "px")
                .style("min-width", "90px")
                .style("border", "1px solid black");
              })
            .on("mouseout", function(evt) {
              tooltipDiv.transition()
                .duration(500)
                .style('opacity', 0);
              })

          legend.append("rect")
            .attr("x", 80*draw_index)
            .attr("y", height+40)
            .attr("width", 10)
            .attr("height", 10)
            .style("fill", chartColors[draw_index]);

          legend.append("text")
            .attr("x", 80*draw_index + 15)
            .attr("y", height+48)
            .text(scenario_key)
        });                                             // ---------------END SCENARIO AGAIN--------------------
      });                                               // ---------------END METRIC--------------------
    });                                                 // ---------------END TOPIC --------------------
  } else {
    $('#accordion-metrics').hide();
    $('#no-metrics-message').show();
  }

}

// add listeners to checkboxes to toggle adding/removing data from graphs by ID
$('input:checkbox').on('change', function(e) {
  $('svg').remove();
  loadGraphs();

});

$(document).ready(function() {
  loadGraphs();
});
