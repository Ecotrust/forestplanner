window.addEventListener( 'load', function() {

  function generatePropertyReport() {
    var hash = window.location.hash.replace('#map=', '');
    var parts = hash.split('/');
    if (parts.length === 5) {
      // landmapper.zoom = parseInt(parts[0], 10);
      // landmapper.center = [
      //   parseFloat(parts[1]),
      //   parseFloat(parts[2])
      // ];
      // landmapper.rotation = parseFloat(parts[3]);
      taxlots = parts[4].split('&');
    }
    console.log(taxlots);

  }

  const formGenerateReport = document.getElementById('form-property-name');
  formGenerateReport.addEventListener('submit', function(e) {
    e.preventDefault();
    generatePropertyReport();
  });
});
