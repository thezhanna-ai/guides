(function () {
  'use strict';

  // Keep account collection limited to Referrer, with sessions disabled.
  const GOATCOUNTER_ENDPOINT = 'https://provovoe.goatcounter.com/count';
  if (!/^https:\/\/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.goatcounter\.com\/count$/.test(GOATCOUNTER_ENDPOINT)) return;
  if (window.location.hostname !== 'pronovoe.com' || window.location.protocol !== 'https:') return;
  if (typeof window.fetch !== 'function') return;

  function send(path, event, referrer) {
    const query = new URLSearchParams({ p: path, ns: 'true' });
    if (event) query.set('e', 'true');
    else query.set('r', referrer);
    // No third-party script, visitor ID, cookies, storage, screen data or query
    // parameters. ns also bypasses sessions if the account setting is missed.
    window.fetch(GOATCOUNTER_ENDPOINT + '?' + query, {
      method: 'GET',
      mode: 'cors',
      credentials: 'omit',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      keepalive: true
    }).catch(function () { /* Analytics must never interrupt reading. */ });
  }

  function start() {
    let referrer = '';
    try {
      const source = new URL(document.referrer);
      if (source.protocol === 'https:' || source.protocol === 'http:') referrer = source.origin;
    } catch (_) { /* A direct opening has no referrer. */ }
    send(window.location.pathname, false, referrer);

    if (typeof window.IntersectionObserver === 'function') {
      let shown = false;
      const observer = new window.IntersectionObserver(function (entries) {
        if (shown || !entries.some(function (entry) { return entry.isIntersecting; })) return;
        shown = true;
        observer.disconnect();
        send('reklama-pokaz', true);
      });
      document.querySelectorAll('section.cta').forEach(function (section) { observer.observe(section); });
    }

    function countClick(event) {
      if (event.button !== (event.type === 'auxclick' ? 1 : 0)) return;
      const target = event.target;
      const element = target && (target.closest ? target : target.parentElement);
      const link = element && element.closest('a[href]');
      if (!link) return;
      try {
        const url = new URL(link.href);
        if ((url.protocol === 'https:' || url.protocol === 'http:') && url.hostname === 'theivansergeev.com') {
          send('reklama-klik', true);
        }
      } catch (_) { /* An invalid link is not an advertising click. */ }
    }
    document.addEventListener('click', countClick);
    document.addEventListener('auxclick', countClick);
  }

  if (document.prerendering) {
    document.addEventListener('prerenderingchange', start, { once: true });
  } else {
    start();
  }
}());
