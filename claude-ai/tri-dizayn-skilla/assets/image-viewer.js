(function () {
  'use strict';
  // Общий lifecycle для существующих div-viewer и native dialog, без смены их оформления
  window.GuideImageViewer = {
    mount: function (viewer, requestClose) {
      var active = false;
      var previousFocus;
      var previousOverflow;
      var background = [];
      var closeButton = viewer.querySelector('.viewer-close');
      var scroll = viewer.querySelector('.viewer-scroll');
      if (scroll) scroll.tabIndex = 0;

      function restore() {
        if (!active) return;
        active = false;
        background.forEach(function (item) { item.element.inert = item.inert; });
        background = [];
        document.body.style.overflow = previousOverflow;
        if (previousFocus && previousFocus.isConnected) previousFocus.focus();
      }

      function open(source) {
        if (active) return;
        var focused = document.activeElement;
        var shot = source && source.closest('.shot');
        previousFocus = shot && !shot.contains(focused) ? shot.querySelector('.zoom') : focused;
        previousOverflow = document.body.style.overflow;
        active = true;
        if (viewer.tagName === 'DIALOG') viewer.showModal();
        else viewer.setAttribute('open', '');
        viewer.setAttribute('aria-hidden', 'false');
        // Если viewer вложен в оболочку страницы, блокируем соседей на каждом уровне,
        // но не его предков: inert на предке сделал бы сам viewer недоступным
        var branch = viewer;
        while (branch.parentElement) {
          Array.prototype.forEach.call(branch.parentElement.children, function (element) {
            if (element === branch) return;
            background.push({element: element, inert: element.inert});
            element.inert = true;
          });
          if (branch.parentElement === document.body) break;
          branch = branch.parentElement;
        }
        document.body.style.overflow = 'hidden';
        closeButton.focus();
      }

      function close() {
        if (!active) return false;
        if (viewer.tagName === 'DIALOG') viewer.close();
        else viewer.removeAttribute('open');
        viewer.setAttribute('aria-hidden', 'true');
        restore();
        return true;
      }

      document.addEventListener('keydown', function (event) {
        if (!active) return;
        if (event.key === 'Escape') {
          event.preventDefault();
          event.stopImmediatePropagation();
          requestClose();
          return;
        }
        if (event.key !== 'Tab') return;
        // Пересчитываем список: скрытые/disabled элементы не должны задерживать Tab
        var focusable = Array.prototype.filter.call(viewer.querySelectorAll('button, a[href], input, select, textarea, [tabindex]'), function (element) {
          return !element.disabled && !element.inert && element.tabIndex >= 0 && element.getClientRects().length;
        });
        var first = focusable[0] || closeButton;
        var last = focusable[focusable.length - 1] || closeButton;
        var focused = document.activeElement;
        if (!viewer.contains(focused) || (event.shiftKey ? focused === first : focused === last)) {
          event.preventDefault();
          (event.shiftKey ? last : first).focus();
        }
        // Старые локальные traps не должны перехватывать Tab повторно
        event.stopImmediatePropagation();
      }, true);
      viewer.addEventListener('cancel', function (event) { event.preventDefault(); requestClose(); });
      viewer.addEventListener('close', function () {
        // close доставляется отдельной задачей: к этому времени диалог мог открыться снова
        if (!viewer.hasAttribute('open')) restore();
      });
      return {open: open, close: close};
    }
  };
})();
