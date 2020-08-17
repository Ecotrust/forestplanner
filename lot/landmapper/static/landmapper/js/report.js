document.querySelector('.copy-link').addEventListener('click', function(e) {
  var url = window.location.href
  const el = document.createElement('textarea');
  el.value = url;
  document.body.appendChild(el);
  el.select();
  document.execCommand('copy');
  document.body.removeChild(el);
})
