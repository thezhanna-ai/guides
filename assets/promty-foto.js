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
  var viewerModal = GuideImageViewer.mount(viewer, closeViewer);
  function closeViewer() { viewerModal.close(); big.removeAttribute('src'); }
  document.querySelectorAll('.shot .zoom').forEach(function (button) {
    button.addEventListener('click', function () {
      var img = button.parentElement.querySelector('img');

      big.src = img.dataset.fullSrc || img.currentSrc || img.src;
      big.alt = img.alt;
      viewerModal.open(img);
      closeButton.focus();
    });
  });
  closeButton.addEventListener('click', function () { closeViewer(); });
  viewer.addEventListener('click', function (event) {
    if (event.target !== viewer) return;
    var rect = viewer.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom) closeViewer();
  });
  viewer.addEventListener('close', function () {
    if (!viewer.hasAttribute('open')) big.removeAttribute('src');
  });
})();
