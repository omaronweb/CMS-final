// Prototype only (Omar, 2026-10-19): this copy holds just the «المحتوى» step, so
// anything that leaves it (logo, السابق, المتابعة, مساعدة) opens the full wizard
// in Claude Design instead.
(function () {
  var FULL = 'https://claude.ai/design/p/04eea629-3a9f-4684-859a-7ae9b3a90d0a?file=wizard%2F01-paths.html';
  document.addEventListener('click', function (e) {
    var el = e.target.closest('a[href]:not([href^="#"]), #nextBtn, .help-btn');
    if (!el || el.closest('#proto-pages')) return; // the prototype bar keeps its links
    e.preventDefault();
    e.stopImmediatePropagation();
    location.href = FULL;
  }, true);
})();
