(function () {
  'use strict';
  var viewer = document.createElement('dialog');
  viewer.className = 'image-viewer';
  viewer.setAttribute('aria-label', 'Картинка крупнее');
  var closeButton = document.createElement('button');
  closeButton.className = 'viewer-close';
  closeButton.type = 'button';
  closeButton.textContent = 'Закрыть';
  var big = document.createElement('img');
  big.alt = '';
  viewer.appendChild(closeButton);
  viewer.appendChild(big);
  document.body.appendChild(viewer);
  var previousFocus;
  document.querySelectorAll('.shot .zoom').forEach(function (button) {
    button.addEventListener('click', function () {
      var img = button.parentElement.querySelector('img');
      previousFocus = button;
      big.src = img.currentSrc || img.src;
      big.alt = img.alt;
      viewer.showModal();
      closeButton.focus();
    });
  });
  closeButton.addEventListener('click', function () { viewer.close(); });
  viewer.addEventListener('click', function (event) {
    if (event.target !== viewer) return;
    var rect = viewer.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom) viewer.close();
  });
  viewer.addEventListener('close', function () {
    big.removeAttribute('src');
    if (previousFocus) previousFocus.focus();
  });
})();
