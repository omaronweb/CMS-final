/* Prototype pages bar for the doc pages (columns table, excerpt guide,
   improvements list), so they link back to the CMS pages. The CMS pages build
   the same bar in proto.js; keep the two page lists in sync. */
(function () {
  'use strict';
  var PAGES = [
    ['index.html', 'الرئيسية'],
    ['edit__post_type-article.html', 'قائمة المقالات'],
    ['post-new__post_type-article.html', 'أضف مقالة'],
    ['post__action-edit__lang-ar__post-272.html', 'تحرير مقالة'],
    ['content-types.html', 'أنواع المحتوى'],
    ['edit-tags__post_type-article__taxonomy-topic.html', 'البيانات الوصفية'],
    ['edit-tags__post_type-article__taxonomy-article-type.html', 'المجموعات'],
    ['post__action-edit__post-702.html', 'الإعدادات العامة'],
    ['homepage.html', 'واجهة الموقع'],
    ['list-pages-columns.html', 'أعمدة القوائم'],
    ['improvements.html', 'قائمة التحسينات']
  ];
  // links are relative to the prototype root, where this script lives
  var base = (document.currentScript && document.currentScript.src || '').replace(/[^/]*$/, '');
  var here = new URL(location.href).pathname.split('/').pop() || 'index.html';

  var css = document.createElement('style');
  css.textContent =
    '#proto-pages{position:fixed;bottom:16px;inset-inline-end:16px;z-index:9999999;display:flex;flex-wrap:wrap;' +
    'align-items:center;gap:4px;max-width:calc(100vw - 32px);padding:6px 10px;border-radius:12px;' +
    'background:rgba(0,0,0,.88);box-shadow:0 4px 24px rgba(0,0,0,.35);font:13px/1.5 "IBM Plex Sans Arabic",-apple-system,"Segoe UI",Tahoma,sans-serif;direction:rtl}' +
    '#proto-pages .proto-pages-label{color:rgba(255,255,255,.6);margin-inline-end:4px}' +
    '#proto-pages a{color:#fff;text-decoration:none;padding:4px 10px;border-radius:8px}' +
    '#proto-pages a:hover{background:rgba(255,255,255,.12)}' +
    '#proto-pages a.is-current{background:#c49a2a;color:#0f1a2e;font-weight:600}' +
    'body{padding-bottom:96px}';
  document.head.appendChild(css);

  var nav = document.createElement('nav');
  nav.id = 'proto-pages';
  nav.setAttribute('aria-label', 'Prototype pages');
  nav.innerHTML = '<span class="proto-pages-label">صفحات مختارة:</span>' +
    PAGES.map(function (p) {
      return '<a href="' + base + p[0] + '"' + (p[0] === here ? ' class="is-current" aria-current="page"' : '') + '>' + p[1] + '</a>';
    }).join('');
  document.body.appendChild(nav);
})();
