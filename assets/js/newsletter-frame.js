/* Circular Textile Alliance — newsletter relay.
   Runs inside newsletter-frame.html, which index.html frames with
   sandbox="allow-scripts" and nothing else, so this document's origin is
   opaque. That is the point: Mailchimp answers JSONP, and a JSONP reply is a
   script that runs with the full rights of the document that loads it. Loaded
   here, it can reach nothing that matters — not the page, not its storage,
   not any other page on the site's origin — and all it can hand back is a
   message, which the page treats as untrusted text.

   Protocol (postMessage, both ways):
     frame → page  { relay: 'ready' }
     page → frame  { relay: 'subscribe', id, action, fields }
     frame → page  { relay: 'reply', id, ok, result, msg } */
(function () {
  'use strict';

  var HOST = 'https://circulartextilealliance.us16.list-manage.com';
  var callbacks = 0;

  var reply = function (id, data) {
    window.parent.postMessage({
      relay: 'reply',
      id: id,
      ok: Boolean(data),
      result: data ? String(data.result || '') : '',
      msg: data && data.msg != null ? String(data.msg) : ''
    }, '*');
  };

  window.addEventListener('message', function (event) {
    if (event.source !== window.parent) return;
    var request = event.data;
    if (!request || request.relay !== 'subscribe' || typeof request.id !== 'number') return;

    // Only ever the hosted signup on Mailchimp's host, turned into its JSONP
    // twin. (The CSP would refuse anything else anyway.)
    var url;
    try { url = new URL(String(request.action)); } catch (e) { return reply(request.id, null); }
    if (url.origin !== HOST || url.pathname !== '/subscribe/post') return reply(request.id, null);
    url.pathname = '/subscribe/post-json';

    var fields = request.fields || {};
    Object.keys(fields).forEach(function (key) {
      url.searchParams.set(key, String(fields[key]));
    });

    // One uniquely named global per request; the first of callback, error,
    // or load-without-callback settles it.
    var name = 'relay' + (++callbacks);
    var script = document.createElement('script');
    var settled = false;
    var settle = function (data) {
      if (settled) return;
      settled = true;
      window[name] = function () {};
      script.remove();
      reply(request.id, data);
    };
    window[name] = settle;
    url.searchParams.set('c', name);
    script.src = url.href;
    script.onerror = function () { settle(null); };
    script.onload = function () { settle(null); };
    document.head.appendChild(script);
  });

  window.parent.postMessage({ relay: 'ready' }, '*');
})();
