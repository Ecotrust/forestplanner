var drawSource = new ol.source.Vector({wrapX: false});

var drawVector = new ol.layer.Vector({
  source: drawSource
});

var overlayGroupName = "Overlays";

var map = new ol.Map({
  target: 'map',
  layers: [
    new ol.layer.Group({
      'title': 'Base maps',
      layers: [
        new ol.layer.Tile({
          title: 'Open Street Map',
          source: new ol.source.OSM(),
          name: 'OSM Base Layer',
          type: 'base',
          visible: false
        }),
        new ol.layer.Tile({
          title: 'ESRI Topo Map',
          source: new ol.source.XYZ({
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}.png',
            attributions: 'Sources: Esri, HERE, Garmin, Intermap, increment P Corp., GEBCO, USGS, FAO, NPS, NRCAN, GeoBase, IGN, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), swisstopo, © OpenStreetMap contributors, and the GIS User Community'
          }),
          name: 'ESRI Topo',
          type: 'base',
          visible: false
        }),
        new ol.layer.Tile({
          // preload: Infinity,
          title: 'Satellite Imagery',
          source: new ol.source.XYZ({
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attributions: 'Sources: Esri, DigitalGlobe, Earthstar Geographics, CNES/Airbus DS, GeoEye, USDA FSA, USGS, Getmapping, Aerogrid, IGN, IGP, and the GIS User Community'
          }),
          name: 'Satellite',
          type: 'base',
          visible: false
        }),
        new ol.layer.Tile({
          title: 'Hybrid',
          source: new ol.source.XYZ({
            url: 'https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v11/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoiZWNvdHJ1c3RkZXYiLCJhIjoiY2o1aXE1dmp2MWxjZjJ3bG16MHQ1YnBlaiJ9.tnv1SK2iNlFXHN_78mx5oA',
            attributions: "Tiles &copy; <a href='http://mapbox.com/'>MapBox</a>"
          }),
          name: 'Hybrid',
          type: 'base'
        })
      ],
    }),
    new ol.layer.Group({
      title: overlayGroupName,
      layers: [
        new ol.layer.Tile({
          title: 'Wetlands',
          source: new ol.source.XYZ({
            url: 'http://{a-d}.tiles.ecotrust.org/tiles/LOT_wetlands/{z}/{x}/{y}.png'
          }),
          name: 'Wetlands',
          legend: {
            id: 'wetland-legend',
            image: '/media/img/legends/LOT_wetlands.png'
          },
          visible: false
        }),
        new ol.layer.Tile({
          title: 'Stream Buffers',
          source: new ol.source.XYZ({
            url: 'http://{a-d}.tiles.ecotrust.org/tiles/LOT_streambuffers/{z}/{x}/{y}.png'
          }),
          name: 'Stream Buffers',
          legend: {
            id: 'stream-buffers-legend',
            image: '/media/img/legends/LOT_streambuffers.png'
          },
          visible: false
        }),
        new ol.layer.Tile({
          title: 'Streams',
          source: new ol.source.XYZ({
            url: 'http://{a-d}.tiles.ecotrust.org/tiles/LOT_streams/{z}/{x}/{y}.png'
          }),
          name: 'Streams',
          legend: {
            id: 'streams-legend',
            image: '/media/img/legends/LOT_streams.png'
          },
          visible: false
        })
      ]
    }),
    drawVector
  ],
  view: new ol.View({
    center: ol.proj.fromLonLat([-121.9, 45.5]),
    zoom: 7
  })
});

var layerSwitcher = new ol.control.LayerSwitcher({
   tipLabel: 'Layers' // Optional label for button
});
map.addControl(layerSwitcher);

// Focus map on OR & WA
// initExtent4326 = [-125,41.9,-116.4,49];
// Allow map to fit "most" of the region if it's close
initExtent4326 = [-124,43,-117.4,48];
[xmin,ymin] = ol.proj.fromLonLat([initExtent4326[0],initExtent4326[1]]);
[xmax,ymax] = ol.proj.fromLonLat([initExtent4326[2],initExtent4326[3]]);
var initExtent = [xmin,ymin,xmax,ymax];
map.getView().fit(initExtent , map.getSize());

// Show/Hide legend in legend panel when toggling overlay visibility
var layer_groups = map.getLayers().getArray();
for (var i = 0; i < layer_groups.length; i++) {
  if (layer_groups[i].get('title') == overlayGroupName) {
    overlays = layer_groups[i].getLayers().getArray();
    for (var j = 0; j < overlays.length; j++) {
      overlays[j].on('change:visible', function(e) {
        if (e.oldValue) {
          $('#' + e.target.get('legend').id).remove();
        } else {
          $('#map-legend').append('<div id="' + e.target.get('legend').id + '">' +
            '<img src="' + e.target.get('legend').image + '">');
        }
        if ($('#map-legend').html() == '') {
          $('#map-legend-wrapper').hide();
        } else {
          $('#map-legend-wrapper').show();
        }
      });
    }
  }
}

drawInteraction = new ol.interaction.Draw({
  source: drawSource,
  type: "Polygon"
});

drawInteraction.on('drawend', function(e) {
  stopDrawing();
  standDrawn(e);
});

drawModify = new ol.interaction.Modify(
  {
    source: drawSource
  }
);

drawModify.on('modifyend', function(e) {
  standModified(e);
});

drawSnap = new ol.interaction.Snap(
  {
    source: drawSource
  }
);

standFormValid = function() {
  response = '';
  if ($('#id_name').val() == '') {
    response += 'Please give your stand a name.\n';
  }
  if ($('#id_geometry_final').val() == '') {
    response += 'No drawing detected. Please "Start Over".\n';
  }
  return response;
};

standFormChange = function() {
  response = standFormValid();
  if (response == '') {
    $('#collect-data-advance-button').removeClass('disabled');
  } else {
    $('#collect-data-advance-button').addClass('disabled');
  }
};

standFormSubmitted = function(e) {
  e.preventDefault();
  response = standFormValid();
  url = '/features/discoverystand/form/';
  if (window.location.pathname.indexOf("/discovery/map/") >= 0) {
    uid = window.location.pathname.split("/discovery/map/")[1];
    if (uid != null && uid != "") {
      url = '/features/discoverystand/' + uid;
    }
  }
  if (response == '') {
    $.ajax({
      url: url,
      data: $('#stand-form').serialize(),
      method: 'POST',
      success: function(data){
        var uid = JSON.parse(data)['X-Madrona-Show'];
        window.location = '/discovery/collect_data/' + uid;
      },
      error: function(data){
        alert("Submit error! (" + data.status + ") " + + data.statusText + ": " + data.responseText);;
      }
    });
  } else {
    alert(response);
  }
}

startDrawing();

$('#stand-form').on('change', standFormChange);
$('#id_name').on('change', standFormChange);
$('#id_geometry_final').on('change', standFormChange);
$('#collect-data-advance-button').on('click', standFormSubmitted);
