/* Street Hustle CCG card editor — scaffold bootstrap (issue #3).
 *
 * Scope of this file: the shell is alive — tabs switch, zoom works, and the
 * canvas renders its empty state from the design tokens. Card data, art
 * upload, and export are deliberately NOT here; they arrive in later issues.
 */
(function () {
  "use strict";

  var ZOOM_MIN = 0.5;
  var ZOOM_MAX = 2;
  var ZOOM_STEP = 0.1;

  var state = {
    zoom: 1,
    card: null, // no card loaded yet — that is the point of the scaffold
  };

  var stage = document.getElementById("canvas-stage");
  var placeholder = document.getElementById("canvas-placeholder");
  var zoomLabel = document.getElementById("zoom-label");
  var statusCards = document.getElementById("status-cards");

  /* -- tabs ------------------------------------------------------------ */
  function initTabs() {
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));
    var panels = Array.prototype.slice.call(document.querySelectorAll(".tab-panel"));

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var target = tab.getAttribute("data-tab");
        tabs.forEach(function (t) {
          t.setAttribute("aria-selected", String(t === tab));
        });
        panels.forEach(function (panel) {
          panel.hidden = panel.getAttribute("data-panel") !== target;
        });
      });
    });
  }

  /* -- zoom ------------------------------------------------------------ */
  function applyZoom() {
    if (stage) stage.style.transform = "scale(" + state.zoom + ")";
    if (zoomLabel) zoomLabel.textContent = Math.round(state.zoom * 100) + "%";
  }

  function initZoom() {
    var out = document.getElementById("zoom-out");
    var inBtn = document.getElementById("zoom-in");

    if (out) {
      out.addEventListener("click", function () {
        state.zoom = Math.max(ZOOM_MIN, +(state.zoom - ZOOM_STEP).toFixed(2));
        applyZoom();
      });
    }
    if (inBtn) {
      inBtn.addEventListener("click", function () {
        state.zoom = Math.min(ZOOM_MAX, +(state.zoom + ZOOM_STEP).toFixed(2));
        applyZoom();
      });
    }
    applyZoom();
  }

  /* -- canvas ---------------------------------------------------------- */
  function render() {
    if (!stage || !placeholder) return;
    placeholder.hidden = Boolean(state.card);
    if (statusCards) {
      statusCards.textContent = state.card ? "1 card loaded" : "0 cards loaded";
    }
  }

  /* -- public surface for later issues --------------------------------- */
  window.SHCCGEditor = {
    state: state,
    /** Load a card object into the canvas (implemented in a later issue). */
    loadCard: function (card) {
      state.card = card || null;
      render();
      return state.card;
    },
    getState: function () {
      return state;
    },
    render: render,
  };

  // Neutralise anything the shell might have double-declared, then boot.
  initTabs();
  initZoom();
  render();

  document.documentElement.setAttribute("data-scaffold-ready", "true");
})();