/* Circular Textile Alliance — progressive enhancement.
   Everything below is additive: with JS disabled the page still renders and
   reads correctly. The header simply stays in its over-hero state and the
   mobile menu falls back to being always-visible (see the `no-js` note in
   site.css if you change that). */
(function () {
  'use strict';

  /* --- Header: swap to the light, scrolled treatment past 40px ----------- */
  var header = document.getElementById('site-header');
  if (header) {
    var ticking = false;
    var sync = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 40);
      ticking = false;
    };
    window.addEventListener('scroll', function () {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(sync);
      }
    }, { passive: true });
    sync();
  }

  /* --- Mobile disclosure menu ------------------------------------------- */
  var toggle = document.getElementById('nav-toggle');
  var menu = document.getElementById('nav-mobile');

  if (toggle && menu) {
    var setOpen = function (open) {
      toggle.setAttribute('aria-expanded', String(open));
      menu.hidden = !open;
    };

    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    // Following an in-page link should dismiss the menu.
    menu.addEventListener('click', function (event) {
      if (event.target.closest('a')) setOpen(false);
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        toggle.focus();
      }
    });

    // The menu is a panel hanging off the right of the bar rather than a sheet
    // covering the page, so a click beside it reads as dismissal.
    document.addEventListener('click', function (event) {
      if (toggle.getAttribute('aria-expanded') !== 'true') return;
      if (event.target.closest('#nav-mobile, #nav-toggle')) return;
      setOpen(false);
    });

    // Widening past the `lg` breakpoint reveals the desktop nav; leaving the
    // disclosure open would then show both.
    var desktop = window.matchMedia('(min-width: 64em)');
    var onBreakpoint = function (event) { if (event.matches) setOpen(false); };
    if (desktop.addEventListener) desktop.addEventListener('change', onBreakpoint);
    else desktop.addListener(onBreakpoint);   // Safari < 14
  }

  /* --- Policy dialogs ----------------------------------------------------
     <dialog>.showModal() handles centring, the backdrop, focus containment and
     Escape; the animation is CSS. With JS off the buttons simply do nothing,
     which is the same as the inert placeholders they replaced. */
  var openers = document.querySelectorAll('.policy-open');
  Array.prototype.forEach.call(openers, function (button) {
    button.addEventListener('click', function () {
      var dialog = document.getElementById(button.getAttribute('data-policy'));
      if (dialog && typeof dialog.showModal === 'function') dialog.showModal();
    });
  });

  // Clicking the backdrop closes. The backdrop is not a child, so a click on
  // the dialog element itself but outside .policy__inner is the signal.
  Array.prototype.forEach.call(document.querySelectorAll('.policy'), function (dialog) {
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) dialog.close();
    });
  });

  /* --- Newsletter ------------------------------------------------------
     Both forms are complete without this: they post to Mailchimp's hosted
     signup page in a new tab. With script, the same fields go to Mailchimp's
     post-json endpoint instead, so the answer appears in the form's own status
     line and the visitor stays on the page.

     Mailchimp sends no CORS headers, so its answer can only be read as JSONP,
     and a JSONP reply is a script that runs with the rights of whatever
     document loads it. So this page never loads it. Each request goes through
     newsletter-frame.html in a sandboxed frame (allow-scripts, no
     allow-same-origin): an opaque origin of its own, from which the reply can
     reach nothing here or anywhere else on the site's origin. All the frame
     can hand back is a message, and Mailchimp's wording in it is only ever
     matched against known answers, never shown. This page's CSP admits no
     third-party script at all.

     If the frame doesn't start, Mailchimp can't be reached or doesn't answer,
     or the answer is one we don't recognise (a captcha, say), the next press of
     Subscribe goes through natively and finishes on Mailchimp's own page. */
  var READY_MS = 4000;      // the relay frame announcing itself
  var TIMEOUT_MS = 15000;   // Mailchimp answering
  var LATE_MS = 60000;      // how long a late answer still counts
  var GRACE_MS = 2000;      // ignore repeat presses just after a handoff

  // One line at the form's 26rem width, two on a phone — the height
  // .newsletter__status reserves. tests/browser/newsletter.cjs measures each.
  var MESSAGES = {
    invalid: 'Please enter a valid email address.',
    sending: 'Subscribing…',
    confirm: 'Almost done — please confirm via the email we just sent.',
    subscribed: 'Thank you — you’re subscribed.',
    already: 'You’re already subscribed — thank you!',
    tooMany: 'Too many attempts — please try again in a few minutes.',
    offline: 'Couldn’t reach Mailchimp — press Subscribe to finish there.',
    captcha: 'One more step — press Subscribe to finish on Mailchimp.',
    unknown: 'Mailchimp didn’t accept that — press Subscribe to see why.',
    handoff: 'Continuing on Mailchimp’s page, in a new tab.'
  };
  var FAILED = { fallback: true, text: MESSAGES.offline };

  // Mailchimp's reply is { result: 'success' | 'error', msg: <HTML> }.
  var interpret = function (reply) {
    if (!reply) return FAILED;
    var msg = String(reply.msg || '');
    // Mailchimp says this both as an error and, with a profile update, as a
    // success ("You're already subscribed, your profile has been updated.").
    if (/already subscribed/i.test(msg)) return { done: true, text: MESSAGES.already };
    if (reply.result === 'success') {
      return { done: true, text: /confirm/i.test(msg) ? MESSAGES.confirm : MESSAGES.subscribed };
    }
    if (/too many/i.test(msg)) return { text: MESSAGES.tooMany };
    if (/fake or invalid|single @|portion of the email|valid email|enter a value/i.test(msg)) {
      return { text: MESSAGES.invalid };
    }
    if (/captcha/i.test(msg)) return { fallback: true, text: MESSAGES.captcha };
    return { fallback: true, text: MESSAGES.unknown };
  };

  // One sandboxed frame per request, removed once it has answered. Returns a
  // function that removes it early. onReply gets { result, msg } or null.
  var relays = 0;
  var relay = function (action, fields, onReady, onReply) {
    var id = ++relays;
    var frame = document.createElement('iframe');
    var listener = function (event) {
      if (event.source !== frame.contentWindow) return;
      var data = event.data || {};
      if (data.relay === 'ready') {
        onReady();
        // The frame's origin is opaque, so '*' is the only target there is;
        // event.source has already pinned the recipient to this frame.
        frame.contentWindow.postMessage({ relay: 'subscribe', id: id, action: action, fields: fields }, '*');
      } else if (data.relay === 'reply' && data.id === id) {
        close();
        onReply(data.ok ? { result: String(data.result), msg: String(data.msg) } : null);
      }
    };
    var close = function () {
      window.removeEventListener('message', listener);
      frame.remove();
    };
    window.addEventListener('message', listener);
    frame.setAttribute('sandbox', 'allow-scripts');
    frame.setAttribute('aria-hidden', 'true');
    frame.title = 'Newsletter relay';
    frame.tabIndex = -1;
    frame.hidden = true;
    frame.src = 'newsletter-frame.html';
    document.body.appendChild(frame);
    return close;
  };

  // There are two of these forms on the home page, so each one finds its own
  // field and status from inside itself rather than by a page-wide id.
  var forms = document.querySelectorAll('.newsletter__form');
  Array.prototype.forEach.call(forms, function (form) {
    var field = form.querySelector('.newsletter__input');
    var status = form.querySelector('.newsletter__status');
    if (!field || !status || !form.getAttribute('action')) return;

    var busy = false;      // a request is in flight
    var native = false;    // the next submit goes to Mailchimp's own page
    var handedOff = 0;     // when it last did
    var sent = '';         // the address most recently sent

    // The script validates and words its own error, in the status line, so the
    // browser's bubble is turned off — but only once this has run: without
    // script the markup still asks the browser to check the address.
    form.noValidate = true;

    var say = function (text) { status.textContent = text; };
    var settle = function (outcome) {
      busy = false;
      field.readOnly = false;
      form.removeAttribute('aria-busy');
      native = Boolean(outcome.fallback);
      // Clear only what was sent, not something typed since.
      if (outcome.done && field.value.trim() === sent) field.value = '';
      say(outcome.text);
    };

    form.addEventListener('submit', function (event) {
      // In flight, or just handed to Mailchimp: a double click or a held Enter
      // must not start a second request or open a second tab.
      if (busy || Date.now() - handedOff < GRACE_MS) {
        event.preventDefault();
        return;
      }
      var email = field.value.trim();
      if (!email || !field.checkValidity()) {
        event.preventDefault();
        say(MESSAGES.invalid);
        field.focus();
        return;
      }
      field.value = email;

      if (native) {
        // Let this submit open the hosted page, which a click is allowed to do.
        native = false;
        handedOff = Date.now();
        say(MESSAGES.handoff);
        return;
      }

      event.preventDefault();
      busy = true;
      sent = email;
      field.readOnly = true;
      form.setAttribute('aria-busy', 'true');
      say(MESSAGES.sending);

      var fields = {};
      new FormData(form).forEach(function (value, key) { fields[key] = String(value); });

      var gaveUp = false;
      var giveUp = function () {
        if (gaveUp) return;
        gaveUp = true;
        window.clearTimeout(notReady);
        window.clearTimeout(noAnswer);
        settle(FAILED);
        // Hold the relay open a while: a slow success still counts (below).
        window.setTimeout(close, LATE_MS);
      };
      var close = relay(form.action, fields, function () {
        window.clearTimeout(notReady);
      }, function (reply) {
        var outcome = interpret(reply);
        if (!gaveUp) {
          gaveUp = true;
          window.clearTimeout(notReady);
          window.clearTimeout(noAnswer);
          settle(outcome);
        } else if (outcome.done && native && !busy) {
          // Answered after we gave up, and the visitor hasn't acted on the
          // fallback since: the signup went through after all.
          settle(outcome);
        }
      });
      var notReady = window.setTimeout(giveUp, READY_MS);
      var noAnswer = window.setTimeout(giveUp, TIMEOUT_MS);
    });
  });
})();
