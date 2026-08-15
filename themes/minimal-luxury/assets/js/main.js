/* minimal-luxury — small, dependency-free behaviours
   1. mobile menu overlay
   2. scroll reveal (IntersectionObserver)
   3. "Copy" text button on code blocks
*/
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;

  /* ---------- 1. Menu overlay ---------- */
  var openBtn = doc.querySelector('[data-menu-open]');
  var closeBtn = doc.querySelector('[data-menu-close]');
  var overlay = doc.querySelector('[data-menu]');

  function setMenu(open) {
    if (!overlay) return;
    overlay.classList.toggle('is-open', open);
    overlay.setAttribute('aria-hidden', open ? 'false' : 'true');
    doc.body.classList.toggle('is-locked', open);
    if (openBtn) openBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open && closeBtn) closeBtn.focus();
    if (!open && openBtn) openBtn.focus();
  }

  if (openBtn && overlay) {
    openBtn.addEventListener('click', function () { setMenu(true); });
    if (closeBtn) closeBtn.addEventListener('click', function () { setMenu(false); });
    overlay.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') setMenu(false);
    });
    doc.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && overlay.classList.contains('is-open')) setMenu(false);
    });
  }

  /* ---------- 2. Scroll reveal ---------- */
  var reveals = doc.querySelectorAll('.reveal');
  if (reveals.length) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-in');
            io.unobserve(entry.target);
          }
        });
      }, { rootMargin: '0px 0px -6% 0px', threshold: 0.02 });
      reveals.forEach(function (el) { io.observe(el); });
    } else {
      reveals.forEach(function (el) { el.classList.add('is-in'); });
    }
  }

  /* ---------- 3. Copy buttons ---------- */
  var pres = doc.querySelectorAll('.prose pre');
  if (pres.length && navigator.clipboard) {
    pres.forEach(function (pre) {
      var host = pre.closest('.highlight');
      if (!host) {
        host = doc.createElement('div');
        host.className = 'code-block';
        pre.parentNode.insertBefore(host, pre);
        host.appendChild(pre);
      }
      if (host.querySelector('.copy-btn')) return;
      var btn = doc.createElement('button');
      btn.type = 'button';
      btn.className = 'copy-btn';
      btn.textContent = 'Copy';
      btn.setAttribute('aria-label', 'Copy code to clipboard');
      btn.addEventListener('click', function () {
        var code = pre.querySelector('code');
        var text = (code || pre).innerText.replace(/\n$/, '');
        navigator.clipboard.writeText(text).then(function () {
          btn.textContent = 'Copied';
          btn.classList.add('is-done');
          setTimeout(function () {
            btn.textContent = 'Copy';
            btn.classList.remove('is-done');
          }, 1800);
        });
      });
      host.appendChild(btn);
    });
  }

  root.classList.add('js-ready');
})();
