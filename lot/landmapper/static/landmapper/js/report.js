var shareLinks = document.querySelectorAll('.copy-link');
for (var i = 0; i < shareLinks.length; i++) {
  shareLinks[i].addEventListener('click', function(e) {
    var mapDiv = e.target.closest('.section-report');
    var url = window.location.href
    const el = document.createElement('textarea');
    el.value = url.split('#')[0] + '#' + mapDiv.id;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    window.alert('URL has been copied to your clipboard')
  })
}
