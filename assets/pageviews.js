(function () {
  'use strict';

  // Set only after the owner registers GoatCounter and disables all data
  // collection except Referrer. Empty means no requests, including in drafts.
  const GOATCOUNTER_ENDPOINT = '';
  if (!/^https:\/\/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.goatcounter\.com\/count$/.test(GOATCOUNTER_ENDPOINT)) return;
  if (window.location.hostname !== 'pronovoe.com' || window.location.protocol !== 'https:') return;
  if (typeof window.fetch !== 'function') return;

  function countOpening() {
    let referrer = '';
    try {
      const source = new URL(document.referrer);
      if (source.protocol === 'https:' || source.protocol === 'http:') referrer = source.origin;
    } catch (_) { /* A direct opening has no referrer. */ }

    const query = new URLSearchParams({
      p: window.location.pathname,
      r: referrer,
      ns: 'true'
    });
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

  if (document.prerendering) {
    document.addEventListener('prerenderingchange', countOpening, { once: true });
  } else {
    countOpening();
  }
}());
