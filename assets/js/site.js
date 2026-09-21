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

  /* --- Newsletter --------------------------------------------------------
     There is no subscription endpoint yet. Claiming success would be a lie and
     letting the form navigate would drop the address on the floor, so the
     submit is intercepted and reported honestly. To go live: give the <form> a
     real `action`/`method` and delete this block. */
  var form = document.getElementById('newsletter-form');
  var status = document.getElementById('newsletter-status');

  if (form && status) {
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var field = document.getElementById('newsletter-email');
      var value = field && field.value.trim();

      // Both messages are kept to a single line at the form's 26rem width, so
      // they fit the height reserved for .newsletter__status and the panel
      // never grows on submit.
      if (!value || !field.checkValidity()) {
        status.textContent = 'Please enter a valid email address.';
        if (field) field.focus();
        return;
      }
      status.textContent = 'Subscriptions aren’t live yet — nothing was recorded.';
    });
  }
})();
