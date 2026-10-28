/* Общий со статьями выбор темы; применяется до отрисовки главной. */
(() => {
  const root = document.documentElement;
  let saved = 'light';
  try { saved = localStorage.getItem('guide-theme') === 'dark' ? 'dark' : 'light'; } catch (_) {}
  root.dataset.theme = saved;

  document.addEventListener('DOMContentLoaded', () => {
    const button = document.querySelector('.theme-toggle');
    function updateButton() {
      const dark = root.dataset.theme === 'dark';
      button.textContent = dark ? '☀' : '◐';
      button.setAttribute('aria-pressed', String(dark));
    }
    updateButton();
    button.addEventListener('click', () => {
      root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('guide-theme', root.dataset.theme); } catch (_) {}
      updateButton();
    });
  });
})();
