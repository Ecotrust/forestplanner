$(document).ready(function() {

  // Turn stand_stats species basal area data into format easily understood by d3
  var species_data = [];
  for (var i =0; i < Object.keys(stand_stats.basal_area_dict.species).length; i++) {
    key = Object.keys(stand_stats.basal_area_dict.species)[i];
    species_data.push(
      {
        'label': key,
        'value': stand_stats.basal_area_dict.species[key]
      }
    );
  }

  var data = species_data;

  // a lot of the below code was copied and altered from https://www.tutorialsteacher.com/d3js/create-pie-chart-using-d3js
  var svg = d3.select("#species-pie-chart"),
      width = 150,
      height = 150,
      radius = Math.min(width, height) / 2,
      g = svg.append("g").attr("transform", "translate(" + 150 + "," + 110 + ")");

  var color = d3.schemeCategory10;

  // Generate the pie
  var pie = d3.pie().value(function(d) {
    return d.value;
  });

  // Generate the arcs
  path = d3.arc()
              .innerRadius(0)
              .outerRadius(radius);

  label = d3.arc()
              .innerRadius(radius - 80)
              .outerRadius(radius);

  percent = d3.arc()
              .innerRadius(20)
              .outerRadius(radius);

  //Generate groups
  arc = g.selectAll("arc")
              .data(pie(data))
              .enter()
              .append("g")
              .attr("class", "arc")

  //Draw arc paths
  arc.append("path")
      .attr("fill", function(d, i) {
          return color[i % color.length];
      })
      .attr("d", path);

  // push the labels outside of the chart
  // this section borrowed from nrabinowitz here: https://stackoverflow.com/a/8198247
  arc.append("text")
      .attr("transform", function(d) {
          var c = label.centroid(d);
          var x = c[0];
          var y = c[1];
          // pythagorean theorem for hypotenuse
          var h = Math.sqrt(x*x + y*y);
          var labelr = radius + 20;
          return "translate(" + (x/h * labelr) + "," + (y/h * labelr) + ")";
      })
      .text(function(d) {return d.data.label});

  arc.append("text")
    .attr("transform", function(d) {
      return "translate(" + percent.centroid(d) + ")";
    })
    .text(function(d) {
      return (parseFloat(d.data.value)/stand_stats.basal_area_dict.total*100).toFixed(1) + "%";
    })

});
