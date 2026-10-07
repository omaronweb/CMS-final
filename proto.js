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
      say('\u0647\u0630\u0647 \u0627\u0644\u0635\u0641\u062D\u0629 \u0644\u064A\u0633\u062A \u0645\u0646 \u0627\u0644\u0646\u0645\u0648\u0630\u062C \u2014 \u0627\u0633\u062A\u062E\u062F\u0645 \u0635\u0641\u062D\u0627\u062A \u0627\u0644\u0646\u0645\u0648\u0630\u062C \u0623\u0633\u0641\u0644 \u0627\u0644\u0634\u0627\u0634\u0629');
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
  // Side boxes except Publish start collapsed (CMS-improvements), and open on click
  if (!body.classList.contains('post-type-book-series')) {
    $$('#postbox-container-1 .postbox:not(#submitdiv)').forEach(function (box) {
      box.classList.add('closed');
      var b = $('.handlediv', box); if (b) b.setAttribute('aria-expanded', 'false');
    });
  }
  $$('.postbox .handlediv, .postbox .hndle').forEach(function (h) {
    h.addEventListener('click', function (e) {
      if (e.target.closest('.handle-order-higher, .handle-order-lower, a')) return;
      var box = h.closest('.postbox');
      box.classList.toggle('closed');
      var b = $('.handlediv', box); if (b) b.setAttribute('aria-expanded', String(!box.classList.contains('closed')));
    });
  });

  // Screen Options column checkboxes show / hide their column, as in WordPress
  $$('.hide-column-tog').forEach(function (cb) {
    cb.addEventListener('change', function () {
      $$('.column-' + cb.value).forEach(function (c) { c.classList.toggle('hidden', !cb.checked); });
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
  $$('.page-title-action, .split-page-title-action a, #wp-link-submit, .form-wrap h2').forEach(function (el) {
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
  // Article fields: every add button (images, audio, video, PDF, clip, Word) just says أضف
  $$('.acf-repeater-add-row').forEach(function (btn) { btn.textContent = 'أضف'; });
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
    // only taxonomies with parents (الوسوم، الكلمات المفتاحية، القراء have none)
    if (!$('#addtag #parent, #edittag #parent')) return;
    // Check we're on a taxonomy page (edit-tags)
    var isTaxPage = document.body.className.indexOf('edit-tags') !== -1
      || window.location.href.indexOf('edit-tags') !== -1
      || !!$('#the-list');
    if (!isTaxPage || !$('.taxonomy-topic, .taxonomy-fiqhi-topic, .taxonomy-index, [class*="taxonomy-"]')) {
      // Broader check: are we on an edit-tags page?
      if (!$$('form#edittag, form#posts-filter').length) return;
    }
    // Apply hierarchy: nested children and grandchildren under the first row, then a parent
    // whose three children are siblings next to each other with no children of their own
    var levels = [0, 1, 2, 1, 2, 3, 0, 1, 1, 1, 0, 0]; // pattern for the first 12 rows
    for (var i = 0; i < Math.min(rows.length, levels.length); i++) {
      var lvl = levels[i];
      rows[i].className = rows[i].className.replace(/level-\d+/, 'level-' + lvl);
    }
  })();

  // ACF field-group meta boxes get the acf-postbox class from ACF's JS on the live CMS
  // (and its .inside the acf-fields -top classes when the page was captured without them)
  $$('.postbox[id^="acf-group_"]').forEach(function (box) {
    box.classList.add('acf-postbox');
    var inside = $(':scope > .inside', box);
    if (inside && !inside.classList.contains('acf-fields')) inside.classList.add('acf-fields', '-top');
  });

  // ACF accordions — what ACF's JS does on the live CMS: the fields after an accordion
  // (up to the next accordion) move into it, behind a clickable title.
  // An accordion marked as an endpoint only closes the group and is removed.
  $$('.acf-field-accordion').forEach(function (acc) {
    var fieldsEl = $('.acf-input > .acf-fields', acc);
    if (!fieldsEl) return;
    var next = acc.nextElementSibling;
    if (fieldsEl.getAttribute('data-endpoint') === '1') { acc.remove(); return; }
    while (next && next.classList.contains('acf-field') && !next.classList.contains('acf-field-accordion')) {
      var n = next.nextElementSibling;
      fieldsEl.appendChild(next);
      next = n;
    }
    var open = fieldsEl.getAttribute('data-open') === '1';
    var labelWrap = $(':scope > .acf-label', acc);
    var title = document.createElement('div');
    title.className = 'acf-accordion-title';
    title.innerHTML = '<i class="acf-accordion-icon dashicons"></i>' + (labelWrap ? labelWrap.innerHTML : '');
    var parent = acc.parentNode;
    fieldsEl.classList.add('acf-accordion-content');
    if (parent && parent.classList.contains('-left')) fieldsEl.classList.add('-left'); else fieldsEl.classList.add('-top');
    acc.innerHTML = '';
    acc.appendChild(title);
    acc.appendChild(fieldsEl);
    acc.classList.add('acf-accordion');
    function sync() {
      acc.classList.toggle('-open', open);
      fieldsEl.style.display = open ? '' : 'none'; // ACF shows/hides the content inline
      $('.acf-accordion-icon', title).className = 'acf-accordion-icon dashicons dashicons-arrow-' + (open ? 'down' : (document.dir === 'rtl' || body.classList.contains('rtl') ? 'left' : 'right'));
    }
    sync();
    title.addEventListener('click', function () { open = !open; sync(); });
  });

  // ACF conditional logic — hide fields whose conditions are not met, as on the live CMS
  (function () {
    var conditional = $$('.acf-field[data-conditions]');
    if (!conditional.length) return;
    function valueOf(field) {
      if (!field) return [];
      var input = $(':scope > .acf-input', field) || field;
      var sel = $('select', input);
      if (sel) return $$('option', sel).filter(function (o) { return o.selected; }).map(function (o) { return o.value; });
      var checks = $$('input[type=radio], input[type=checkbox]', input);
      if (checks.length) return checks.filter(function (c) { return c.checked; }).map(function (c) { return c.value; });
      var txt = $('input, textarea', input);
      return txt && txt.value ? [txt.value] : [];
    }
    function findField(from, key) {
      var scope = from.parentNode;
      while (scope) {
        var hit = scope.querySelector ? scope.querySelector('.acf-field[data-key="' + key + '"]') : null;
        if (hit) return hit;
        scope = scope.parentNode;
      }
      return null;
    }
    function test(rule, from) {
      var v = valueOf(findField(from, rule.field));
      switch (rule.operator) {
        case '==': return v.indexOf(String(rule.value)) !== -1;
        case '!=': return v.indexOf(String(rule.value)) === -1;
        case '==empty': return !v.length || v.every(function (x) { return x === ''; });
        case '!=empty': return v.some(function (x) { return x !== ''; });
        case '==contains': return v.join(' ').indexOf(rule.value) !== -1;
        case '!=contains': return v.join(' ').indexOf(rule.value) === -1;
        default: return true;
      }
    }
    function run() {
      conditional.forEach(function (f) {
        var groups;
        try { groups = JSON.parse(f.getAttribute('data-conditions')); } catch (e) { return; }
        var show = groups.some(function (and) { return and.every(function (r) { return test(r, f); }); });
        f.classList.toggle('acf-hidden', !show);
      });
    }
    run();
    document.addEventListener('change', function (e) { if (e.target.closest('.acf-field')) run(); });
  })();

  // Excerpt (المقتطف) — point "أعرف أكثر عن المقتطف" link to the Arabic guide
  (function () {
    var box = document.getElementById('postexcerpt');
    if (!box) return;
    var link = box.querySelector('.inside a.proto-dead');
    if (!link) return;
    link.href = 'docs/excerpt.html';
    link.target = '_blank';
    link.className = '';
    link.style.cssText = 'color:#2563eb;text-decoration:none;font-weight:500;';
  })();

  // ── Font (saved choice) ─────────────
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

    var savedFont = localStorage.getItem('mushkat-font') || 'default';

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


    // Prototype pages — the only pages included in CMS-final, one click away
    // (the doc pages build the same bar with proto-bar.js; keep both lists in sync)
    var protoPages = [
      ['index.html', 'الرئيسية'],                          // الرئيسية
      ['edit__post_type-article.html', 'قائمة المقالات'], // قائمة المقالات
      ['post-new__post_type-article.html', 'أضف مقالة'],     // أضف مقالة
      ['post__action-edit__lang-ar__post-272.html', 'تحرير مقالة'], // تحرير مقالة
      ['content-types.html', 'أنواع المحتوى'], // قائمة وإضافة وتحرير لكل نوع محتوى
      ['edit-tags__post_type-article__taxonomy-topic.html', 'البيانات الوصفية'], // البيانات الوصفية
      ['edit-tags__post_type-article__taxonomy-article-type.html', 'المجموعات'], // المجموعات
      ['post__action-edit__post-702.html', 'الإعدادات العامة'], // الإعدادات العامة
      ['homepage.html', 'واجهة الموقع'], // الصفحة الرئيسية للموقع
      ['list-pages-columns.html', 'أعمدة القوائم'], // أعمدة صفحات القوائم
      ['improvements.html', 'قائمة التحسينات'] // ما تغيّر مقارنةً بـ cms-testing، للمطوّر
    ];
    var here = (location.pathname.split('/').pop() || 'index.html');
    var nav = document.createElement('nav');
    nav.id = 'proto-pages';
    nav.setAttribute('aria-label', 'Prototype pages');
    nav.innerHTML = '<span class="proto-pages-label">صفحات مختارة:</span>' +
      protoPages.map(function (p) {
        return '<a href="' + p[0] + '"' + (p[0] === here ? ' class="is-current" aria-current="page"' : '') + '>' + p[1] + '</a>';
      }).join('');
    body.appendChild(nav);
  })();


  // ── المجموعات (formerly الأنواع) and القراء are taxonomies like the others: their
  // pages sit under البيانات الوصفية (القراء used to sit under the audio books item), and
  // Add / Edit has an المجموعات box to put the item in a group
  (function () {
    var here = (location.pathname.split('/').pop() || 'index.html');
    var cats = $('#toplevel_page_edit-tags-taxonomy-topic .wp-submenu');
    if (!cats) return;
    [['edit-tags__post_type-article__taxonomy-article-type.html', 'المجموعات', 'menu-posts-article', /taxonomy-article-type\.html$/],
     ['edit-tags__post_type-audio-book-lesson__taxonomy-reciter.html', 'القراء', 'menu-posts-audio-book-series', /taxonomy-reciter\.html$/]
    ].forEach(function (t) {
      // the old link elsewhere in the menu goes away
      $$('#adminmenu .wp-submenu a[href="' + t[0] + '"], #adminmenu .wp-submenu a[data-orig-href="' + t[0] + '"]').forEach(function (a) {
        if (!cats.contains(a)) a.parentNode.remove();
      });
      var on = t[3].test(here);
      var g = document.createElement('li');
      if (on) g.className = 'current';
      g.innerHTML = '<a href="' + t[0] + '">' + t[1] + '</a>';
      cats.appendChild(g);
      if (!on) return;
      var top = document.getElementById('toplevel_page_edit-tags-taxonomy-topic');
      [top, $('a', top)].forEach(function (el) {
        el.classList.remove('wp-not-current-submenu'); el.classList.add('wp-has-current-submenu', 'wp-menu-open');
      });
      // the page belongs to البيانات الوصفية, not to a content type
      var other = document.getElementById(t[2]);
      if (other) [other, $('a', other)].forEach(function (el) {
        el.classList.remove('wp-has-current-submenu', 'wp-menu-open'); el.classList.add('wp-not-current-submenu');
      });
    });
  })();

  // ── Bulk edit on the list pages: with 2+ rows checked, a bar under the header
  // offers «تعديل … لـN عناصر» under each column that can be changed for many rows
  // at once (title, status, taxonomies); other columns get nothing.
  (function () {
    var table = $('table.wp-list-table.posts');
    var head = table && $('thead tr', table);
    if (!head || !$('#the-list')) return;
    var TERMS = {
      'taxonomy-topic': ['آداب الإسلام', 'آداب وأخلاق', 'أصول الفقه', 'الأخلاق'],
      'taxonomy-fiqhi-topic': ['الطهارة', 'الصلاة', 'الصيام', 'الزكاة'],
      'taxonomy-keyword': ['القرآن', 'التربية', 'الأسرة', 'الرقائق'],
      'taxonomy-article-type': ['المقالات', 'الأبحاث', 'الخواطر']
    };
    var STATUSES = ['منشور', 'مسودة', 'بانتظار المراجعة', 'خاص'];
    function kindOf(th) {
      if (th.classList.contains('column-title')) return 'title';
      if (th.textContent.replace(/Sort (ascending|descending)\.?/g, '').trim() === 'حالة النشر') return 'status';
      var tax = Array.prototype.filter.call(th.classList, function (c) { return /^column-taxonomy-/.test(c); })[0];
      return tax ? tax.replace('column-', '') : null;
    }
    var bar = document.createElement('tr');
    bar.className = 'cms-bulk-bar';
    bar.hidden = true;
    $$('th, td', head).forEach(function (th) {
      var cell = document.createElement('td');
      cell.className = Array.prototype.filter.call(th.classList, function (c) {
        return /^column-/.test(c) || c === 'hidden' || c === 'check-column';
      }).join(' ');
      var kind = kindOf(th);
      if (kind) {
        var name = th.textContent.replace(/Sort (ascending|descending)\.?/g, '').trim();
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'button cms-bulk-btn';
        b.dataset.kind = kind;
        b.dataset.name = name;
        b.dataset.col = (Array.prototype.filter.call(th.classList, function (c) { return /^column-(?!primary)/.test(c) && c !== 'column-cb'; })[0] || '');
        cell.appendChild(b);
      }
      bar.appendChild(cell);
    });
    head.parentNode.appendChild(bar);

    function checkedRows() {
      return $$('#the-list > tr').filter(function (tr) {
        var c = $('.check-column input[type=checkbox]', tr);
        return c && c.checked && !tr.hidden && tr.offsetParent !== null;
      });
    }
    // terms of a taxonomy without a demo list: the ones already in that column
    function termsIn(col) {
      var seen = [];
      $$('#the-list td.' + col + ' a').forEach(function (a) {
        var t = a.textContent.trim();
        if (t && seen.indexOf(t) === -1) seen.push(t);
      });
      return seen;
    }
    function itemsLabel(n) { return n === 2 ? 'عنصرين' : n + (n <= 10 ? ' عناصر' : ' عنصرًا'); }
    function countLabel(n) { return n === 2 ? 'لعنصرين' : 'لـ' + n + (n <= 10 ? ' عناصر' : ' عنصرًا'); }
    function refresh() {
      var n = checkedRows().length;
      bar.hidden = n < 2;
      $$('.cms-bulk-btn', bar).forEach(function (b) { b.textContent = 'تعديل ' + itemsLabel(n); });
    }
    table.addEventListener('change', function () { setTimeout(refresh, 0); });

    // The dialog: one control per kind of column
    var dlg = document.createElement('div');
    dlg.className = 'cms-bulk-dialog';
    dlg.hidden = true;
    body.appendChild(dlg);
    function close() { dlg.hidden = true; }
    dlg.addEventListener('click', function (e) { if (e.target === dlg || e.target.closest('[data-close]')) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

    bar.addEventListener('click', function (e) {
      var b = e.target.closest('.cms-bulk-btn');
      if (!b) return;
      var rows = checkedRows(), kind = b.dataset.kind, field;
      if (kind === 'title') {
        field = '<label>ابحث عن<input type="text" data-f="find"></label><label>استبدل بـ<input type="text" data-f="repl"></label>';
      } else if (kind === 'status') {
        field = '<label>الحالة الجديدة<select data-f="val">' + STATUSES.map(function (v) { return '<option>' + v + '</option>'; }).join('') + '</select></label>';
      } else {
        field = '<label>الإجراء<select data-f="op"><option value="add">إضافة</option><option value="remove">إزالة</option></select></label>' +
          '<label>' + b.dataset.name + '<select data-f="val">' + (TERMS[kind] || termsIn(b.dataset.col)).map(function (v) { return '<option>' + v + '</option>'; }).join('') + '</select></label>';
      }
      dlg.innerHTML = '<div class="cms-bulk-panel" role="dialog" aria-modal="true">' +
        '<h2>تعديل ' + b.dataset.name + ' ' + countLabel(rows.length) + '</h2>' +
        '<ul class="cms-bulk-list">' + rows.map(function (tr) { var t = $('.row-title', tr); return '<li>' + (t ? t.textContent : '') + '</li>'; }).join('') + '</ul>' +
        field +
        '<div class="cms-bulk-actions"><button type="button" class="button button-primary" data-apply>تطبيق</button><button type="button" class="button" data-close>إلغاء</button></div></div>';
      dlg.hidden = false;
      var first = $('input, select', dlg); if (first) first.focus();
      $('[data-apply]', dlg).addEventListener('click', function () {
        var get = function (f) { var el = $('[data-f="' + f + '"]', dlg); return el ? el.value : ''; };
        rows.forEach(function (tr) {
          var cell = b.dataset.col && $('td.' + b.dataset.col, tr);
          if (kind === 'title') {
            var t = $('.row-title', tr);
            if (t && get('find')) t.textContent = t.textContent.split(get('find')).join(get('repl'));
          } else if (kind === 'status') {
            if (cell) cell.textContent = get('val');
          } else if (cell) {
            var terms = $$('a', cell).map(function (a) { return a.textContent.trim(); });
            var v = get('val');
            if (get('op') === 'add' && terms.indexOf(v) === -1) terms.push(v);
            if (get('op') === 'remove') terms = terms.filter(function (x) { return x !== v; });
            cell.innerHTML = terms.length ? terms.map(function (x) { return '<a href="#">' + x + '</a>'; }).join('، ') : '<span aria-hidden="true">—</span>';
          }
        });
        close();
        say('تم تعديل ' + b.dataset.name + ' ' + countLabel(rows.length) + ' (في النموذج فقط)');
      });
    });
    refresh();
  })();
  // ── Above list tables: التنسيق الشرطي and إعادة تعيين الترتيب sit behind a text link
  // («عرض خيارات إضافية» / «إخفاء الخيارات الإضافية»), next to the filters, so the
  // item count stays at the end of the bar, in line with the count under the table.
  (function () {
    var ac = document.getElementById('ac-table-actions');
    var nav = ac && ac.closest('.tablenav');
    // only where there are options to show (the topics pages have none)
    if (!nav || !$('.ac-table-actions-buttons > *', ac)) return;
    var box = document.createElement('div');
    box.className = 'alignleft actions cms-more';
    var link = document.createElement('a');
    link.href = '#';
    link.className = 'cms-more-toggle';
    link.setAttribute('aria-expanded', 'false');
    link.textContent = 'عرض خيارات إضافية';
    box.appendChild(link);
    box.appendChild(ac);
    var filters = $$('.alignleft.actions:not(.bulkactions)', nav).pop();
    if (filters) filters.parentNode.insertBefore(box, filters.nextSibling);
    else nav.insertBefore(box, nav.firstChild);
    link.addEventListener('click', function (e) {
      e.preventDefault();
      var open = box.classList.toggle('is-open');
      link.setAttribute('aria-expanded', String(open));
      link.textContent = open ? 'إخفاء الخيارات الإضافية' : 'عرض خيارات إضافية';
    });
  })();
  // ── شجرة التصنيفات on Add / Edit: the terms sit under four parents (الموضوعية،
  // الفقهية، العقدية، الفنون), at most three terms each; typing in «فلترة...» lists the matching terms, each with its
  // parent's name in parentheses.
  (function () {
    var list = document.getElementById('topicchecklist');
    if (!list) return;
    var PARENTS = [
      { name: 'التصنيفات الموضوعية', terms: null },
      { name: 'التصنيفات الفقهية', terms: ['أصول الفقه', 'الفقه وأصوله', 'سنن وأحكام', 'حقوق وواجبات'] },
      { name: 'التصنيفات العقدية', terms: ['عقائد ونبوات', 'دورة العقيدة الواسطية'] },
      // الفنون has its own box on the live CMS (empty there); here it is a parent
      // with sample terms
      { name: 'الفنون', terms: [], add: ['التفسير', 'الحديث', 'النحو'] }
    ];
    var MAX_CHILDREN = 3;
    var ownText = function (li) {
      if (li.dataset.term) return li.dataset.term;
      var l = $(':scope > label', li);
      return (li.dataset.term = l ? l.textContent.replace(/\s+/g, ' ').trim() : '');
    };
    var roots = $$(':scope > li', list);
    var uls = PARENTS.map(function (p) {
      var li = document.createElement('li');
      li.className = 'cms-tax-parent';
      li.innerHTML = '<label class="selectit"><input type="checkbox"> ' + p.name + '</label><ul class="children"></ul>';
      list.appendChild(li);
      return $('ul', li);
    });
    roots.forEach(function (li) {
      var t = ownText(li);
      var i = PARENTS.findIndex(function (p) { return p.terms && p.terms.indexOf(t) !== -1; });
      uls[i === -1 ? 0 : i].appendChild(li);
    });
    PARENTS.forEach(function (p, i) {
      (p.add || []).forEach(function (t) {
        var li = document.createElement('li');
        li.innerHTML = '<label class="selectit"><input type="checkbox" name="tax_input[topic][]"> ' + t + '</label>';
        uls[i].appendChild(li);
      });
    });
    // at most MAX_CHILDREN terms per parent, checked terms first
    uls.forEach(function (ul) {
      var kids = $$(':scope > li', ul);
      var keep = kids.filter(function (li) { var c = $(':scope > label input', li); return c && c.checked; });
      kids.forEach(function (li) { if (keep.length < MAX_CHILDREN && keep.indexOf(li) === -1) keep.push(li); });
      kids.forEach(function (li) { if (keep.indexOf(li) === -1) li.remove(); });
    });

    // every term carries its parent's name, shown only while filtering
    $$('li', list).forEach(ownText); // names first, before the parent tags join the labels
    $$('li', list).forEach(function (li) {
      var parent = li.parentNode.closest('li');
      var label = $(':scope > label', li);
      if (parent && label) {
        var tag = document.createElement('span');
        tag.className = 'cms-tax-parent-name';
        tag.textContent = ' (' + ownText(parent) + ')';
        label.appendChild(tag);
      }
    });

    var input = $('#taxonomy-topic .zad-tax-filter');
    if (!input) return;
    input.addEventListener('input', function () {
      var q = input.value.trim();
      list.classList.toggle('is-filtering', !!q);
      // show a term when it or one of its children matches; its own row only if it matches
      (function walk(ul) {
        var any = false;
        $$(':scope > li', ul).forEach(function (li) {
          var self = !!q && ownText(li).indexOf(q) !== -1;
          var kids = $(':scope > ul.children', li);
          var below = kids ? walk(kids) : false;
          li.classList.toggle('cms-tax-hit', !q || self);
          li.hidden = !!q && !self && !below;
          if (self || below) any = true;
        });
        return any;
      })(list);
      // the «كل شجرة التصنيفات» tab holds the results
      var all = document.getElementById('topic-all'); var pop = document.getElementById('topic-pop');
      if (q && all && pop) { all.style.display = ''; pop.style.display = 'none'; }
    });
  })();
  // ── ترتيب البيانات الوصفية: drag a term up or down among its siblings (its children
  // move with it); «حفظ الترتيب» (above and below the list) confirms. On the live
  // CMS the order is better saved right after each drop.
  (function () {
    var list = document.getElementById('tto_sortable');
    if (!list) return;
    var dragged = null;
    $$('li.term_type_li', list).forEach(function (li) {
      li.draggable = true;
      li.addEventListener('dragstart', function (e) {
        e.stopPropagation();
        dragged = li;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', li.id);
        setTimeout(function () { li.classList.add('is-dragging'); }, 0);
      });
      li.addEventListener('dragend', function () {
        li.classList.remove('is-dragging');
        dragged = null;
      });
      li.addEventListener('dragover', function (e) {
        // only among siblings: the term keeps its parent
        if (!dragged || dragged === li || dragged.parentNode !== li.parentNode) return;
        e.preventDefault();
        e.stopPropagation();
        var box = $(':scope > .item', li).getBoundingClientRect();
        var after = e.clientY > box.top + box.height / 2;
        li.parentNode.insertBefore(dragged, after ? li.nextSibling : li);
      });
    });
    $$('.save-order').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        say('\u062A\u0645 \u062A\u062D\u062F\u064A\u062B \u062A\u0631\u062A\u064A\u0628 \u0627\u0644\u0639\u0646\u0627\u0635\u0631');
      });
    });
  })();
  // ── Sidebar order: each series and its lessons share one menu item, and
  // the items fall into bordered groups, each sorted alphabetically.
  (function () {
    var menu = document.getElementById('adminmenu');
    if (!menu) return;
    var byId = function (id) { return document.getElementById(id); };
    var rename = function (id, name) {
      var n = byId(id) && $('.wp-menu-name', byId(id));
      if (n) n.firstChild ? (n.firstChild.nodeValue = name) : (n.textContent = name);
      var head = byId(id) && $('.wp-submenu-head', byId(id));
      if (head) head.textContent = name;
    };
    rename('menu-posts-scientific-lesson', 'دروس السلاسل العلمية');
    rename('toplevel_page_tm-menu-main', 'خيارات الترجمة');
    rename('menu-media', 'مكتبة الوسائط');
    rename('toplevel_page_googlesitekit-dashboard', 'أدوات جوجل للموقع');
    rename('menu-posts-interpret-series', 'الدورات');

    // Related pages share one menu item, as on cms-testing: the series menu lists
    // its own pages, then its lessons' pages; the lessons item itself goes away
    var GROUPS = [
      ['menu-posts-book-series', 'menu-posts-book-lesson', ['كل شروح الكتب', 'أضف شرح كتاب', 'كل دروس الكتب المشروحة', 'أضف درس كتاب مشروح']],
      ['menu-posts-scientific-series', 'menu-posts-scientific-lesson', ['كل السلاسل العلمية', 'أضف سلسلة علمية', 'كل الدروس العلمية', 'أضف درس علمي']],
      ['menu-posts-radio-program-series', 'menu-posts-radio-program-lesson', ['كل البرامج الإذاعية', 'أضف برنامج إذاعي', 'كل الدروس الإذاعية', 'أضف درس إذاعي']],
      ['menu-posts-tv-program-series', 'menu-posts-tv-program-lesson', ['كل البرامج التلفزيونية', 'أضف برنامج تلفزيوني', 'كل الدروس التلفزيونية', 'أضف درس تلفزيوني']],
      ['menu-posts-book', 'menu-posts-book-page', ['كل الكتب', 'أضف كتاب', 'كل صفحات الكتب', 'أضف صفحة كتاب']],
      ['menu-posts-book-browser-series', 'menu-posts-book-browser-lesson', ['كل كتب المتصفح', 'أضف كتاب للمتصفح', 'كل دروس المتصفح', 'أضف درس للمتصفح']],
      ['menu-posts-audio-book-series', 'menu-posts-audio-book-lesson', ['كل الكتب الصوتية', 'أضف كتاب صوتي', 'كل دروس الكتب الصوتية', 'أضف درس كتاب صوتي']]
    ];
    var items = function (li) { return $$('.wp-submenu > li:not(.wp-submenu-head)', li); };
    GROUPS.forEach(function (g) {
      var a = byId(g[0]), b = byId(g[1]);
      var sub = a && $('.wp-submenu', a);
      if (!sub || !b) return;
      var own = items(a), theirs = items(b);
      if (own[0]) $('a', own[0]).textContent = g[2][0];
      if (own[1]) $('a', own[1]).textContent = g[2][1];
      theirs.slice(0, 2).forEach(function (li, i) {
        li.classList.remove('wp-first-item'); $$('a', li).forEach(function (x) { x.classList.remove('wp-first-item'); });
        $('a', li).textContent = g[2][2 + i];
        li.dataset.cmsType = g[1]; // the lessons' pages, sorted apart from the series' own
        sub.appendChild(li);
      });
      b.remove();
    });

    // الدورات and دروس الدورات stay as two separate menu items
    [['menu-posts-interpret-series', null, ['كل الدورات', 'أضف دورة']],
     ['menu-posts-interpret-lesson', 'دروس الدورات', ['كل دروس الدورات', 'أضف درس دورة']]].forEach(function (g) {
      var li = byId(g[0]);
      if (!li) return;
      if (g[1]) rename(g[0], g[1]);
      items(li).slice(0, 2).forEach(function (x, i) { $('a', x).textContent = g[2][i]; });
    });

    // Menu groups, each sorted alphabetically («ال» counted), with a border
    // between groups; الرئيسية stays on top
    var MENU = [
      ['menu-posts-article', 'menu-posts-fatwa', 'menu-posts-benefit', 'menu-posts-static-page'],
      ['menu-posts-supplication', 'menu-posts-podcast', 'menu-posts-tilawa', 'menu-posts-speech', 'menu-posts-lesson',
       'menu-posts-interpret-lesson', 'menu-posts-lecture', 'menu-posts-short'],
      ['menu-posts-book', 'menu-posts-audio-book-series', 'menu-posts-audio-book-lesson', 'menu-posts-book-browser-series', 'menu-posts-book-series'],
      ['menu-posts-scientific-series', 'menu-posts-radio-program-series', 'menu-posts-tv-program-series',
       'menu-posts-interpret-series'],
      ['toplevel_page_edit-tags-taxonomy-topic', 'toplevel_page_tm-menu-main', 'menu-media', 'menu-posts-public-config',
       'menu-users', 'menu-comments'],
      ['menu-tools', 'toplevel_page_googlesitekit-dashboard']
    ];
    var coll = new Intl.Collator('ar');
    var key = function (li) {
      var n = $('.wp-menu-name', li);
      return ((n && n.firstChild ? n.firstChild.nodeValue : '') || '').trim();
    };
    var collapse = byId('collapse-menu');
    $$('#adminmenu > li.wp-menu-separator').forEach(function (x) { x.remove(); });
    MENU.forEach(function (ids, gi) {
      ids.map(byId).filter(Boolean)
        .sort(function (x, y) { return coll.compare(key(x), key(y)); })
        .forEach(function (li, i) {
          li.classList.toggle('cms-menu-section', gi > 0 && i === 0);
          menu.insertBefore(li, collapse || null);
        });
    });

    // Submenus sorted the same way. A list page and its «أضف/إضافة» page stay
    // together as a pair, list first, sorted by the list's name without «كل/كافة»
    // («الكل» counts as the menu item's own name). A submenu that holds two content
    // types (series and their lessons) keeps them apart: the series' pages first,
    // then the lessons', each sorted on its own.
    $$('#adminmenu > li.menu-top').forEach(function (top) {
      var sub = $('.wp-submenu', top);
      if (!sub) return;
      var lis = items(top), units = [];
      var text = function (li) { return $('a', li).textContent.trim(); };
      for (var i = 0; i < lis.length; i++) {
        var t = text(lis[i]), next = lis[i + 1] && text(lis[i + 1]);
        var pair = next && /^(أضف|إضافة)(\s|$)/.test(next) && !/^(أضف|إضافة)(\s|$)/.test(t);
        var k = t === 'الكل' ? key(top) : t.replace(/^(كل|كافة)\s+/, '');
        units.push({ key: k, type: lis[i].dataset.cmsType || '', lis: pair ? [lis[i], lis[++i]] : [lis[i]] });
      }
      var types = units.map(function (u) { return u.type; }).filter(function (t, j, all) { return all.indexOf(t) === j; });
      units.sort(function (x, y) {
        return (types.indexOf(x.type) - types.indexOf(y.type)) || coll.compare(x.key, y.key);
      })
        .forEach(function (u) { u.lis.forEach(function (li) { sub.appendChild(li); }); });
    });
  })();
})();
