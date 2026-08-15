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

  /* ---------- 4. Light / dark toggle ---------- */
  var toggles = doc.querySelectorAll('[data-theme-toggle]');
  var meta = doc.querySelector('meta[name="theme-color"]');
  function currentTheme() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }
  function applyTheme(t) {
    root.setAttribute('data-theme', t);
    if (meta) meta.setAttribute('content', t === 'dark' ? '#1a1a18' : '#f4f1ea');
    toggles.forEach(function (b) {
      b.setAttribute('aria-pressed', t === 'dark' ? 'true' : 'false');
      b.setAttribute('aria-label', t === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    });
  }
  if (toggles.length) {
    applyTheme(currentTheme());
    toggles.forEach(function (b) {
      b.addEventListener('click', function () {
        var next = currentTheme() === 'dark' ? 'light' : 'dark';
        root.classList.add('is-switching');
        applyTheme(next);
        try { localStorage.setItem('theme', next); } catch (e) { /* private mode etc. */ }
        setTimeout(function () { root.classList.remove('is-switching'); }, 700);
      });
    });
    function savedTheme() {
      try { var v = localStorage.getItem('theme'); return (v === 'dark' || v === 'light') ? v : null; } catch (err) { return null; }
    }
    function osTheme() {
      return (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
    }
    // follow the OS if the visitor never chose explicitly
    if (window.matchMedia) {
      matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
        if (!savedTheme()) applyTheme(e.matches ? 'dark' : 'light');
      });
    }
    // pages restored from the back/forward cache keep their old DOM — re-sync the theme
    window.addEventListener('pageshow', function (e) {
      if (e.persisted) applyTheme(savedTheme() || osTheme());
    });
    // keep other open tabs in step
    window.addEventListener('storage', function (e) {
      if (e.key === 'theme') applyTheme(savedTheme() || osTheme());
    });
  }

  root.classList.add('js-ready');
})();
