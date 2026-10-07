/* Единственное место для номера счётчика. Пустая строка полностью выключает Метрику */
(() => {
  'use strict';
  const METRIKA_ID = '';
  const KEY = 'pronovoe-analytics-v1';
  const banner = document.getElementById('cookie-banner');
  if (!banner) return;
  let choice = readChoice();
  let loader = null;
  let initialized = false;

  function readChoice() {
    try {
      const value = window.localStorage.getItem(KEY);
      return value === 'accepted' || value === 'declined' ? value : null;
    } catch (_) {
      return null; // Недоступное хранилище не означает согласие
    }
  }

  function reserveSpace() {
    const height = banner.hidden ? 0 : Math.ceil(banner.getBoundingClientRect().height);
    document.documentElement.style.setProperty('--cookie-height', height + 'px');
  }

  function showBanner(show) {
    banner.hidden = !show;
    reserveSpace();
  }

  function loadMetrika() {
    if (choice !== 'accepted' || !/^[1-9]\d*$/.test(METRIKA_ID) ||
        !Number.isSafeInteger(Number(METRIKA_ID)) || loader) return;
    window.ym = window.ym || function () {
      (window.ym.a = window.ym.a || []).push(arguments);
    };
    window.ym.a = window.ym.a || [];
    window.ym.l = Date.now();
    loader = document.createElement('script');
    loader.async = true;
    loader.src = 'https://mc.yandex.ru/metrika/tag.js';
    loader.onload = () => {
      if (choice !== 'accepted') return;
      window.ym(Number(METRIKA_ID), 'init', {
        webvisor: true, clickmap: true, trackLinks: true,
        accurateTrackBounce: true, disableYtm: true
      });
      initialized = true;
    };
    document.head.appendChild(loader);
  }

  function stopMetrika() {
    if (!loader) return;
    if (initialized) window.ym(Number(METRIKA_ID), 'destruct');
    if (window.ym.a) window.ym.a.length = 0;
    loader.remove();
    // Перезагрузка прекращает также обработчики уже загруженной библиотеки
    window.location.reload();
  }

  function choose(value) {
    choice = value;
    try { window.localStorage.setItem(KEY, value); } catch (_) {
      // Выбор действует в этой вкладке; после её закрытия потребуется новый
    }
    showBanner(false);
    if (value === 'accepted') loadMetrika();
    else stopMetrika();
  }

  document.getElementById('cookie-accept').addEventListener('click', () => choose('accepted'));
  document.getElementById('cookie-decline').addEventListener('click', () => choose('declined'));
  document.querySelectorAll('[data-cookie-settings]').forEach(button => {
    button.addEventListener('click', () => {
      showBanner(true);
      document.getElementById('cookie-decline').focus();
    });
  });
  window.addEventListener('storage', event => {
    if (event.key !== KEY && event.key !== null) return;
    choice = readChoice();
    showBanner(choice === null);
    if (choice !== 'accepted') stopMetrika();
    else loadMetrika();
  });
  window.addEventListener('resize', reserveSpace);
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(reserveSpace).observe(banner);
  showBanner(choice === null);
  loadMetrika();
})();
