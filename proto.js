/* Prototype interactions — replaces WordPress admin JS for offline use. */
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var body = document.body;

  // Toast for disabled actions
  var toast = document.createElement('div');
  toast.className = 'proto-toast';
  body.appendChild(toast);
  var tId;
  function say(msg) {
    toast.textContent = msg;
    toast.classList.add('is-visible');
    clearTimeout(tId);
    tId = setTimeout(function () { toast.classList.remove('is-visible'); }, 2200);
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest('a');
    if (a && a.classList.contains('proto-dead')) {
      e.preventDefault();
      say('Not part of prototype: ' + (a.getAttribute('data-orig-href') || '').replace(/^https?:\/\/[^/]+/, ''));
      return;
    }
    if (a && a.getAttribute('href') === '#') e.preventDefault();
  });

  document.addEventListener('submit', function (e) {
    e.preventDefault();
    say('Prototype: form submission disabled');
  });

  // Admin menu flyouts
  $$('#adminmenu li.wp-has-submenu').forEach(function (li) {
    li.addEventListener('mouseenter', function () { li.classList.add('opensub'); });
    li.addEventListener('mouseleave', function () { li.classList.remove('opensub'); });
  });

  // Collapse menu
  var collapse = $('#collapse-button');
  if (collapse) collapse.addEventListener('click', function (e) {
    e.preventDefault();
    body.classList.toggle('folded');
    collapse.setAttribute('aria-expanded', body.classList.contains('folded') ? 'false' : 'true');
  });

  // Mobile menu
  var mt = $('#wp-admin-bar-menu-toggle a');
  if (mt) mt.addEventListener('click', function (e) { e.preventDefault(); $('#wpwrap').classList.toggle('wp-responsive-open'); });

  // Admin bar dropdowns
  $$('#wpadminbar .menupop').forEach(function (li) {
    li.addEventListener('mouseenter', function () { li.classList.add('hover'); });
    li.addEventListener('mouseleave', function () { li.classList.remove('hover'); });
  });

  // Screen options / help
  [['#show-settings-link', '#screen-options-wrap'], ['#contextual-help-link', '#contextual-help-wrap']].forEach(function (p) {
    var btn = $(p[0]), panel = $(p[1]);
    if (!btn || !panel) return;
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var open = panel.style.display === 'block';
      $$('.screen-meta-toggle').forEach(function (t) { t.style.visibility = open ? '' : 'hidden'; });
      btn.parentNode.style.visibility = '';
      panel.style.display = open ? 'none' : 'block';
      panel.classList.toggle('hidden', open);
      $('#screen-meta').style.display = open ? 'none' : 'block';
      btn.classList.toggle('screen-meta-active', !open);
      btn.setAttribute('aria-expanded', String(!open));
    });
  });
  // Help tabs
  $$('.contextual-help-tabs a').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      $$('.contextual-help-tabs .active').forEach(function (x) { x.classList.remove('active'); });
      a.parentNode.classList.add('active');
      $$('.help-tab-content').forEach(function (x) { x.classList.remove('active'); });
      var t = $(a.getAttribute('href')); if (t) t.classList.add('active');
    });
  });

  // Postboxes (meta boxes)
  $$('.postbox .handlediv, .postbox .hndle').forEach(function (h) {
    h.addEventListener('click', function (e) {
      if (e.target.closest('.handle-order-higher, .handle-order-lower, a')) return;
      var box = h.closest('.postbox');
      box.classList.toggle('closed');
      var b = $('.handlediv', box); if (b) b.setAttribute('aria-expanded', String(!box.classList.contains('closed')));
    });
  });

  // Select-all checkboxes in list tables
  $$('#cb-select-all-1, #cb-select-all-2, .check-column input[id^=cb-select-all]').forEach(function (all) {
    all.addEventListener('change', function () {
      var table = all.closest('table');
      $$('tbody .check-column input[type=checkbox]', table).forEach(function (c) { c.checked = all.checked; });
      $$('thead .check-column input, tfoot .check-column input', table).forEach(function (c) { c.checked = all.checked; });
    });
  });

  // Mobile list-table row toggle
  $$('.toggle-row').forEach(function (b) {
    b.addEventListener('click', function () { b.closest('tr').classList.toggle('is-expanded'); });
  });

  // Dismissible notices
  $$('.notice.is-dismissible').forEach(function (n) {
    if (!$('.notice-dismiss', n)) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'notice-dismiss';
      b.innerHTML = '<span class="screen-reader-text">Dismiss</span>';
      n.appendChild(b);
    }
  });
  document.addEventListener('click', function (e) {
    var d = e.target.closest('.notice-dismiss');
    if (d) { var n = d.closest('.notice, .updated, .error'); if (n) n.remove(); }
  });

  // In-page tabs: <a href="#panel"> inside a tab list toggles sibling panels
  $$('.category-tabs a, .wp-tab-bar a, [role=tablist] a[href^="#"], .nav-tab-wrapper a[href^="#"]').forEach(function (a) {
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) !== '#' || href.length < 2) return;
    a.addEventListener('click', function (e) {
      var target = document.getElementById(href.slice(1));
      if (!target) return;
      e.preventDefault();
      var list = a.closest('ul, nav, div');
      $$('a', list).forEach(function (o) {
        var h = o.getAttribute('href'); if (!h || h.charAt(0) !== '#') return;
        var p = document.getElementById(h.slice(1)); if (p && p !== target) p.style.display = 'none';
        o.classList.remove('nav-tab-active'); if (o.parentNode.tagName === 'LI') o.parentNode.classList.remove('tabs', 'wp-tab-active');
      });
      target.style.display = '';
      a.classList.add('nav-tab-active');
      if (a.parentNode.tagName === 'LI') a.parentNode.classList.add('tabs', 'wp-tab-active');
    });
  });

  // Quick-edit / inline links: harmless no-op feedback
  $$('.editinline, .hide-if-no-js button.button-link').forEach(function (b) {
    b.addEventListener('click', function (e) { e.preventDefault(); say('Prototype: inline editing disabled'); });
  });

  // Gutenberg / components panels: toggle open state (content only present if it was open at capture)
  $$('.components-panel__body-toggle').forEach(function (b) {
    b.addEventListener('click', function () {
      var p = b.closest('.components-panel__body');
      p.classList.toggle('is-opened');
      b.setAttribute('aria-expanded', String(p.classList.contains('is-opened')));
    });
  });

  // Media modal / thickbox links can't open offline
  $$('a.thickbox, .insert-media, #set-post-thumbnail').forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); say('Prototype: media library dialog not available offline'); });
  });

  // Rename search button to بحث
  var searchBtn = $('#search-submit');
  if (searchBtn) searchBtn.value = '\u0628\u062D\u062B';

  // Trim "أضف ..." buttons/headings/inputs to just "أضف"
  var addWord = '\u0623\u0636\u0641';
  // Text-content elements (buttons, links, headings)
  $$('.page-title-action, .split-page-title-action a, .insert-media, #wp-link-submit, .form-wrap h2').forEach(function (el) {
    var t = el.textContent.trim();
    if (t.indexOf(addWord) === 0 && t.length > addWord.length) {
      el.textContent = addWord;
    }
  });
  // Input[type=submit] with value attribute
  $$('input[type="submit"]').forEach(function (el) {
    var v = el.value.trim();
    if (v.indexOf(addWord) === 0 && v.length > addWord.length) {
      el.value = addWord;
    }
  });

  // الصور field: make repeater add button secondary, hide description, rename إضافة مقطع → رفع
  $$('.acf-repeater-add-row').forEach(function (btn) {
    // Make secondary (remove button-primary)
    btn.className = btn.className.replace('button-primary', '');
    // Rename إضافة مقطع فيديو → رفع
    if (btn.textContent.trim().indexOf('\u0625\u0636\u0627\u0641\u0629 \u0645\u0642\u0637\u0639') !== -1) {
      btn.textContent = '\u0631\u0641\u0639';
    }
    // Rename إضافة صورة → رفع
    if (btn.textContent.trim().indexOf('\u0625\u0636\u0627\u0641\u0629 \u0635\u0648\u0631\u0629') !== -1) {
      btn.textContent = '\u0631\u0641\u0639';
    }
  });
  // Hide "أضف صورة واحدة أو أكثر." description
  $$('.acf-field-repeater > .acf-input + .description, .acf-field-repeater .acf-input ~ p.description').forEach(function (p) {
    if (p.textContent.indexOf('\u0623\u0636\u0641 \u0635\u0648\u0631\u0629') !== -1) {
      p.style.display = 'none';
    }
  });

  // Demo hierarchy on taxonomy list pages — reclassify some level-0 rows
  // to show parent/child/grandchild indentation
  (function () {
    var rows = $$('#the-list > tr.level-0');
    if (rows.length < 8) return;
    // Check we're on a taxonomy page (edit-tags)
    var isTaxPage = document.body.className.indexOf('edit-tags') !== -1
      || window.location.href.indexOf('edit-tags') !== -1
      || !!$('#the-list');
    if (!isTaxPage || !$('.taxonomy-topic, .taxonomy-fiqhi-topic, .taxonomy-index, [class*="taxonomy-"]')) {
      // Broader check: are we on an edit-tags page?
      if (!$$('form#edittag, form#posts-filter').length) return;
    }
    // Apply hierarchy: rows[1],[2] = children of rows[0]; rows[3] = grandchild of rows[1]
    var levels = [0, 1, 2, 1, 2, 3, 0, 1, 0, 0]; // pattern for first 10 rows
    for (var i = 0; i < Math.min(rows.length, levels.length); i++) {
      var lvl = levels[i];
      rows[i].className = rows[i].className.replace(/level-\d+/, 'level-' + lvl);
    }
  })();

  // Excerpt (المقتطف) — point "أعرف أكثر عن المقتطف" link to GitHub Pages
  (function () {
    var box = document.getElementById('postexcerpt');
    if (!box) return;
    var link = box.querySelector('.inside a.proto-dead');
    if (!link) return;
    link.href = 'https://omasarizad.github.io/aalaam-cms/excerpts.html';
    link.target = '_blank';
    link.className = '';
    link.style.cssText = 'color:#2563eb;text-decoration:none;font-weight:500;';
  })();

  // ── Dark Mode + Font Switcher ─────────────
  (function () {
    var fonts = [
      { id: 'default',  label: 'افتراضي',    family: '' },
      { id: 'ibm',      label: 'IBM Plex',   family: '"IBM Plex Sans Arabic"' },
      { id: 'thmanyah', label: 'ثمانية',      family: '"thmanyah sans"' }
    ];

    // Ensure custom.css is loaded (no version switching needed)
    var customLink = null;
    $$('link[rel="stylesheet"]').forEach(function (link) {
      var href = link.getAttribute('href') || '';
      if (href.match(/custom(-v\d)?\.css$/)) customLink = link;
    });
    if (customLink) customLink.setAttribute('href', 'custom.css');

    // Inject @font-face for portability
    var fontStyle = document.createElement('style');
    fontStyle.textContent =
      '@font-face { font-family: "thmanyah sans"; src: local("thmanyah sans"), url("fonts/thmanyahsans-Regular.otf") format("opentype"); font-weight: 400; font-style: normal; }' +
      '@font-face { font-family: "thmanyah sans"; src: local("thmanyah sans"), url("fonts/thmanyahsans-Medium.otf") format("opentype"); font-weight: 500; font-style: normal; }' +
      '@font-face { font-family: "thmanyah sans"; src: local("thmanyah sans"), url("fonts/thmanyahsans-Bold.otf") format("opentype"); font-weight: 700; font-style: normal; }' +
      '@font-face { font-family: "thmanyah sans"; src: local("thmanyah sans"), url("fonts/thmanyahsans-Light.otf") format("opentype"); font-weight: 300; font-style: normal; }' +
      '@font-face { font-family: "IBM Plex Sans Arabic"; src: local("IBM Plex Sans Arabic"), url("fonts/IBMPlexSansArabic-Regular.ttf") format("truetype"); font-weight: 400; font-style: normal; }' +
      '@font-face { font-family: "IBM Plex Sans Arabic"; src: local("IBM Plex Sans Arabic"), url("fonts/IBMPlexSansArabic-Medium.ttf") format("truetype"); font-weight: 500; font-style: normal; }' +
      '@font-face { font-family: "IBM Plex Sans Arabic"; src: local("IBM Plex Sans Arabic"), url("fonts/IBMPlexSansArabic-Bold.ttf") format("truetype"); font-weight: 700; font-style: normal; }' +
      '@font-face { font-family: "IBM Plex Sans Arabic"; src: local("IBM Plex Sans Arabic"), url("fonts/IBMPlexSansArabic-SemiBold.ttf") format("truetype"); font-weight: 600; font-style: normal; }' +
      '@font-face { font-family: "IBM Plex Sans Arabic"; src: local("IBM Plex Sans Arabic"), url("fonts/IBMPlexSansArabic-Light.ttf") format("truetype"); font-weight: 300; font-style: normal; }';
    document.head.appendChild(fontStyle);

    var darkMode = localStorage.getItem('mushkat-dark-mode') === 'true';
    var savedFont = localStorage.getItem('mushkat-font') || 'default';

    // Apply saved dark mode immediately
    if (darkMode) body.classList.add('dark-mode');

    // Apply saved font immediately
    function applyFont(fontId) {
      var f = fonts.filter(function (x) { return x.id === fontId; })[0];
      if (!f) return;
      var fontEl = document.getElementById('mushkat-font-override');
      if (!fontEl) {
        fontEl = document.createElement('style');
        fontEl.id = 'mushkat-font-override';
        document.head.appendChild(fontEl);
      }
      if (f.family) {
        fontEl.textContent =
          'body, body.rtl, #wpcontent, #wpbody-content, .wrap, .wp-list-table, ' +
          '#adminmenu, #adminmenu .wp-submenu, .postbox, input, textarea, select, button, ' +
          '.acf-field, .acf-label, .tagify, h1, h2, h3, h4, h5, h6 { ' +
          'font-family: ' + f.family + ', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important; }';
      } else {
        fontEl.textContent = '';
      }
    }
    applyFont(savedFont);

    // Build toggle bar — dark mode only
    var bar = document.createElement('div');
    bar.id = 'css-switcher';
    bar.setAttribute('style',
      'position:fixed;bottom:16px;inset-inline-end:16px;z-index:9999999;' +
      'display:flex;align-items:center;padding:6px;border-radius:12px;' +
      'background:rgba(0,0,0,0.88);backdrop-filter:blur(10px);' +
      'box-shadow:0 4px 24px rgba(0,0,0,0.35);font-family:-apple-system,sans-serif;'
    );

    // Dark mode toggle (sun/moon)
    var dmBtn = document.createElement('button');
    dmBtn.id = 'dark-mode-toggle';
    dmBtn.textContent = darkMode ? '\u263E' : '\u2600';
    dmBtn.title = darkMode ? 'Light Mode' : 'Dark Mode';
    dmBtn.setAttribute('style',
      'padding:4px 10px;border:none;border-radius:7px;cursor:pointer;' +
      'font-size:16px;line-height:1;background:transparent;' +
      'color:' + (darkMode ? '#fbbf24' : '#888') + ';transition:all 0.12s ease;'
    );
    dmBtn.addEventListener('click', function () {
      darkMode = !darkMode;
      body.classList.toggle('dark-mode', darkMode);
      localStorage.setItem('mushkat-dark-mode', String(darkMode));
      dmBtn.textContent = darkMode ? '\u263E' : '\u2600';
      dmBtn.title = darkMode ? 'Light Mode' : 'Dark Mode';
      dmBtn.style.color = darkMode ? '#fbbf24' : '#888';
    });
    bar.appendChild(dmBtn);

    body.appendChild(bar);
  })();
})();
