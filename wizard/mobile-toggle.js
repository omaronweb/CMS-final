/* ═══════════════════════════════════════════════════════════
   Aalaam Wizard — Mobile-preview floating toggle
   A FAB that flips the current page between full web view and a
   phone-sized device frame. State persists across wizard pages
   via localStorage, so navigation stays in the chosen mode.
   ═══════════════════════════════════════════════════════════ */
(function () {
  var KEY = "aalaam_mobile_preview";
  // The device-frame iframe element is marked with data-aalaam-device.
  // frameElement persists across in-iframe navigation, so pages the user
  // clicks through inside the frame stay recognized (no nested rebuild).
  try {
    if (window.frameElement && window.frameElement.getAttribute("data-aalaam-device")) return;
  } catch (e) { /* cross-origin: ignore */ }

  var on = localStorage.getItem(KEY) === "1";

  var PHONE_SVG = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="2" width="12" height="20" rx="3"/><path d="M11 18h2"/></svg>';
  var DESKTOP_SVG = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg>';

  function makeFab() {
    var fab = document.createElement("button");
    fab.id = "__mobileFab";
    fab.type = "button";
    fab.setAttribute("aria-label", on ? "العودة لعرض الويب" : "معاينة نسخة الهاتف");
    fab.title = on ? "العودة لعرض الويب" : "معاينة نسخة الهاتف";
    fab.innerHTML = on ? DESKTOP_SVG : PHONE_SVG;
    Object.assign(fab.style, {
      position: "fixed", bottom: "24px", insetInlineStart: "24px",
      width: "52px", height: "52px", borderRadius: "9999px",
      border: "0", cursor: "pointer", zIndex: "100001",
      background: "linear-gradient(135deg, #1F3A5F 0%, #B8863C 97%)",
      color: "#fff", display: "inline-flex", alignItems: "center",
      justifyContent: "center",
      boxShadow: "0 10px 26px -6px rgba(31,58,95,0.5)",
      transition: "transform 0.18s ease"
    });
    fab.addEventListener("mouseenter", function () { fab.style.transform = "translateY(-2px)"; });
    fab.addEventListener("mouseleave", function () { fab.style.transform = "none"; });
    fab.addEventListener("click", function () {
      localStorage.setItem(KEY, on ? "0" : "1");
      location.reload();
    });
    return fab;
  }

  function buildDeviceFrame() {
    var overlay = document.createElement("div");
    overlay.id = "__mobileOverlay";
    Object.assign(overlay.style, {
      position: "fixed", inset: "0", zIndex: "100000",
      background: "radial-gradient(circle at 50% 40%, #2A3E55 0%, #14293F 100%)",
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", gap: "16px",
      padding: "24px"
    });

    var label = document.createElement("div");
    label.textContent = "معاينة نسخة الهاتف · iPhone SE";
    Object.assign(label.style, {
      color: "rgba(255,255,255,0.7)", fontSize: "13px", fontWeight: "600",
      fontFamily: '"IBM Plex Sans Arabic", system-ui, sans-serif',
      letterSpacing: "0.02em"
    });

    var bezel = document.createElement("div");
    // iPhone SE: 375 × 667 logical px
    var scale = Math.min(1, (window.innerHeight - 130) / 667);
    var frameW = 375, frameH = 667;
    Object.assign(bezel.style, {
      width: frameW + "px", height: frameH + "px",
      transform: "scale(" + scale + ")", transformOrigin: "top center",
      background: "#111", borderRadius: "34px", padding: "12px 8px",
      boxShadow: "0 40px 90px -20px rgba(0,0,0,0.6), inset 0 0 0 2px rgba(255,255,255,0.06)",
      position: "relative", flexShrink: "0"
    });

    var iframe = document.createElement("iframe");
    iframe.setAttribute("data-aalaam-device", "1");
    iframe.src = location.href;
    Object.assign(iframe.style, {
      width: "100%", height: "100%", border: "0",
      borderRadius: "24px", background: "#fff", display: "block"
    });

    bezel.appendChild(iframe);
    overlay.appendChild(label);
    overlay.appendChild(bezel);
    document.body.appendChild(overlay);
    document.documentElement.style.overflow = "hidden";
  }

  function init() {
    if (on) buildDeviceFrame();
    document.body.appendChild(makeFab());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
