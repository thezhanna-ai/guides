(() => {
  'use strict';
  document.querySelectorAll('.comparison-slider').forEach(group => {
    const stage = group.querySelector('.comparison-stage');
    const range = group.querySelector('input[type="range"]');
    function update() {
      const value = Number(range.value);
      group.style.setProperty('--split', value + '%');
      range.setAttribute('aria-valuetext', 'Было ' + value + '%, стало ' + (100 - value) + '%');
    }
    function position(event) {
      const rect = stage.getBoundingClientRect();
      range.value = Math.round(Math.max(0, Math.min(100, (event.clientX - rect.left) / rect.width * 100)));
      update();
    }
    let active = null;
    stage.addEventListener('pointerdown', event => {
      if (!event.isPrimary || event.button !== 0) return;
      active = event.pointerId;
      stage.setPointerCapture(active);
      range.focus({preventScroll:true});
      position(event);
    });
    stage.addEventListener('pointermove', event => { if (event.pointerId === active) position(event); });
    stage.addEventListener('pointerup', event => {
      if (event.pointerId !== active) return;
      position(event);
      active = null;
    });
    stage.addEventListener('lostpointercapture', () => { active = null; });
    stage.addEventListener('pointercancel', () => { active = null; });
    stage.addEventListener('dragstart', event => event.preventDefault());
    range.addEventListener('input', update);
    update();
  });
})();
