$(document).ready(function() {
  function loadStratumEntryTable() {
    var createStratumBtn = document.querySelector('button[data-bind="click: createStratum"]');
    console.log(createStratumBtn);
    if (createStratumBtn) {
      createStratumBtn.click();
      window.clearTimeout();
    } else {
      window.setTimeout(function() {
        loadStratumEntryTable();
      }, 1000);
    }
  }
  // not sure why jquery says dom is ready but click() won't work without settimeout below
  // best guess is the knockout observables are not ready yet
  // TODO: Find a better way than settimeout
  window.setTimeout(function() {
    loadStratumEntryTable();
  }, 1000);
});
