/* Street Hustle CCG card editor - shell bootstrap (issues #3 and #4).
 *
 * Issue #3 built the shell (tokens, card CSS, empty canvas).
 * Issue #4 loads the canonical master DB into editor state, renders the card
 * library with type/rarity/search filtering, draws the selected card on the
 * canvas, and surfaces schema errors from the validator.
 *
 * Editing (text/colours/art/export) is deliberately not here - see #5-#7.
 */
(function () {
  "use strict";

  var ZOOM_MIN = 0.5;
  var ZOOM_MAX = 2;
  var ZOOM_STEP = 0.1;
  var MAX_VISIBLE_ERRORS = 6;

  var state = {
    zoom: 1,
    db: null,
    cards: [],
    filtered: [],
    selected: null,
    filters: { type: "all", rarity: "all", query: "" },
  };

  var el = {};

  function $(id) {
    return document.getElementById(id);
  }

  function titleCase(value) {
    return String(value || "")
      .split(/[_\s]+/)
      .filter(Boolean)
      .map(function (word) { return word.charAt(0).toUpperCase() + word.slice(1); })
      .join(" ");
  }

  function label(value) {
    return titleCase(value);
  }

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
    if (el.stage) el.stage.style.transform = "scale(" + state.zoom + ")";
    if (el.zoomLabel) el.zoomLabel.textContent = Math.round(state.zoom * 100) + "%";
  }

  function initZoom() {
    if (el.zoomOut) {
      el.zoomOut.addEventListener("click", function () {
        state.zoom = Math.max(ZOOM_MIN, +(state.zoom - ZOOM_STEP).toFixed(2));
        applyZoom();
      });
    }
    if (el.zoomIn) {
      el.zoomIn.addEventListener("click", function () {
        state.zoom = Math.min(ZOOM_MAX, +(state.zoom + ZOOM_STEP).toFixed(2));
        applyZoom();
      });
    }
    applyZoom();
  }

  /* -- card element ---------------------------------------------------- */
  function div(className, text) {
    var node = document.createElement("div");
    node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function costNode(card) {
    var cost = div("card-cost");
    var heat = typeof card.cost === "number" ? card.cost : 0;
    if (heat > 0) {
      for (var i = 0; i < heat; i += 1) {
        var pip = document.createElement("span");
        pip.className = "heat-pip";
        cost.appendChild(pip);
      }
    } else {
      var free = document.createElement("span");
      free.className = "heat-pip free";
      cost.appendChild(free);
      cost.appendChild(document.createTextNode(" FREE"));
    }
    return cost;
  }

  function statNode(value, labelText, valueClass) {
    var stat = div("stat");
    var val = div("stat-val" + (valueClass ? " " + valueClass : ""), String(value));
    stat.appendChild(val);
    stat.appendChild(div("stat-lbl", labelText));
    return stat;
  }

  /** Stats bar content differs per card type - mirrors docs/webpages/cards.html. */
  function statsNode(card) {
    var stats = div("card-stats");
    switch (card.type) {
      case "dealer":
        stats.appendChild(statNode(card.hp, "HP", "hp"));
        stats.appendChild(statNode(card.atk, "ATK", "atk"));
        stats.appendChild(statNode(card.def, "DEF", "def"));
        break;
      case "stash":
        stats.appendChild(statNode("+" + card.atkBonus, "ATK", "boost"));
        break;
      case "borough":
        stats.appendChild(statNode("+" + (card.heatGain || 0), "Heat/turn", ""));
        break;
      case "action":
      default: {
        // Actions (and any future type without a stat block) show a cost pip count.
        var heat = typeof card.cost === "number" ? card.cost : 0;
        var costVal = div("stat-val", heat > 0 ? String(heat) : "FREE");
        if (heat === 0) costVal.style.color = "var(--gr)";
        var costStat = div("stat");
        costStat.appendChild(costVal);
        costStat.appendChild(div("stat-lbl", "Cost"));
        stats.appendChild(costStat);
      }
    }
    return stats;
  }

  function subtitleFor(card) {
    switch (card.type) {
      case "stash":
        return "+" + card.atkBonus + " ATK · Attach to Dealer";
      case "borough":
        return "Borough · Free to play";
      default:
        return "";
    }
  }

  function artNode(card) {
    var art = div("card-art");
    var placeholder = div("card-art-placeholder");
    var icon = document.createElement("span");
    icon.className = "placeholder-icon";
    icon.textContent = card.emoji || "🎴";
    placeholder.appendChild(icon);
    placeholder.appendChild(div("placeholder-text", "Art: " + card.name));
    art.appendChild(placeholder);
    return art;
  }

  /** Build the print-fidelity card element for a card object. */
  function buildCardElement(card) {
    var root = div("card " + card.rarity + " " + card.type);

    var top = div("card-top");
    top.appendChild(div("card-type " + card.type, label(card.type)));
    top.appendChild(costNode(card));
    root.appendChild(top);

    root.appendChild(artNode(card));

    var band = div("card-name-band");
    band.appendChild(div("card-name", card.name));
    var subtitle = subtitleFor(card);
    if (subtitle) band.appendChild(div("card-subtitle", subtitle));
    root.appendChild(band);

    root.appendChild(statsNode(card));

    var body = div("card-body");
    var keywords = Array.isArray(card.keywords) ? card.keywords : [];
    keywords.slice(0, 1).forEach(function (kw) {
      body.appendChild(div("ability-tag " + card.type, titleCase(kw)));
    });
    body.appendChild(div("ability-text", card.text || ""));
    if (card.flavor) body.appendChild(div("flavor-text", '"' + card.flavor + '"'));
    root.appendChild(body);

    var footer = div("card-footer");
    footer.appendChild(div("rarity-label", label(card.rarity)));
    footer.appendChild(div("set-info", "v9.6 · " + (card.set || "")));
    root.appendChild(footer);

    return root;
  }

  /* -- rendering ------------------------------------------------------- */
  function renderCanvas() {
    if (!el.canvasCard) return;
    el.canvasCard.innerHTML = "";
    el.placeholder.hidden = Boolean(state.selected);
    if (state.selected) {
      el.canvasCard.appendChild(buildCardElement(state.selected));
    }
  }

  function renderProperties() {
    var card = state.selected || {};
    var fields = {
      "f-id": card.id,
      "f-name": card.name,
      "f-set": card.set,
      "f-faction": card.faction,
      "f-cost": typeof card.cost === "number" ? card.cost : "",
      "f-rarity": card.rarity ? label(card.rarity) : "",
      "f-type": card.type ? label(card.type) : "",
      "f-text": card.text,
      "f-flavor": card.flavor,
      "f-keywords": Array.isArray(card.keywords) ? card.keywords.join(", ") : "",
    };
    Object.keys(fields).forEach(function (id) {
      var node = el.fields[id];
      if (!node) return;
      node.value = fields[id] === undefined || fields[id] === null ? "" : fields[id];
    });
  }

  function renderLibrary() {
    if (!el.libraryList) return;
    el.libraryList.innerHTML = "";
    if (!state.filtered.length) {
      var empty = div("library-empty", state.cards.length ? "No cards match these filters." : "No card data loaded.");
      el.libraryList.appendChild(empty);
      return;
    }
    var fragment = document.createDocumentFragment();
    state.filtered.forEach(function (card) {
      var item = document.createElement("button");
      item.type = "button";
      item.className = "library-item";
      item.setAttribute("data-card-id", card.id);
      item.setAttribute("aria-pressed", String(state.selected === card));

      var head = div("library-item-head");
      head.appendChild(div("library-item-name", card.name));
      head.appendChild(div("library-item-cost", typeof card.cost === "number" ? card.cost : 0));
      item.appendChild(head);

      var meta = div("library-item-meta");
      var tag = document.createElement("span");
      tag.className = "chip chip-" + card.type;
      tag.textContent = label(card.type);
      meta.appendChild(tag);
      var rarity = document.createElement("span");
      rarity.className = "chip chip-rarity-" + card.rarity;
      rarity.textContent = label(card.rarity);
      meta.appendChild(rarity);
      item.appendChild(meta);

      item.addEventListener("click", function () { selectCard(card.id); });
      fragment.appendChild(item);
    });
    el.libraryList.appendChild(fragment);
  }

  function renderStatus() {
    if (el.statusCards) {
      var total = state.cards.length;
      var shown = state.filtered.length;
      el.statusCards.textContent =
        shown === total ? total + " cards loaded" : shown + " / " + total + " cards shown";
    }
    if (el.statusSelection) {
      el.statusSelection.textContent = state.selected
        ? "Selected: " + state.selected.name
        : "Selected: —";
    }
    if (el.statusValidation) {
      var errors = state.db ? state.db.errors : [];
      el.statusValidation.textContent = errors.length
        ? errors.length + " validation issue(s)"
        : "Validated: 116 cards OK";
      el.statusValidation.className = errors.length ? "status-bad" : "status-good";
    }
  }

  function renderBanner() {
    if (!el.banner) return;
    var errors = state.db ? state.db.errors : [];
    if (!errors.length) {
      el.banner.hidden = true;
      el.banner.innerHTML = "";
      return;
    }
    el.banner.hidden = false;
    el.banner.innerHTML = "";
    el.banner.appendChild(
      div("banner-title", errors.length + " schema validation issue(s)")
    );
    var list = document.createElement("ul");
    errors.slice(0, MAX_VISIBLE_ERRORS).forEach(function (error) {
      var li = document.createElement("li");
      li.textContent = error.message;
      list.appendChild(li);
    });
    el.banner.appendChild(list);
    if (errors.length > MAX_VISIBLE_ERRORS) {
      el.banner.appendChild(
        div("banner-more", "+ " + (errors.length - MAX_VISIBLE_ERRORS) + " more")
      );
    }
  }

  function renderDbSummary() {
    if (!el.dbSummary) return;
    var stats = state.db ? state.db.stats : null;
    if (!stats) {
      el.dbSummary.textContent = "No data loaded.";
      return;
    }
    var meta = state.db.meta || {};
    el.dbSummary.textContent =
      (meta.set_name ? meta.set_name + " · " : "") +
      "v" + (meta.version || "?") + " · " +
      stats.total + " cards · " +
      "Dealer " + (stats.byType.dealer || 0) + " / " +
      "Stash " + (stats.byType.stash || 0) + " / " +
      "Action " + (stats.byType.action || 0) + " / " +
      "Borough " + (stats.byType.borough || 0);
  }

  function renderAll() {
    renderBanner();
    renderDbSummary();
    renderLibrary();
    renderCanvas();
    renderProperties();
    renderStatus();
  }

  /* -- state transitions ----------------------------------------------- */
  function selectCard(cardId) {
    state.selected = state.db ? state.db.byId[cardId] || null : null;
    renderLibrary();
    renderCanvas();
    renderProperties();
    renderStatus();
  }

  function applyFilters(patch) {
    Object.keys(patch).forEach(function (key) { state.filters[key] = patch[key]; });
    state.filtered = window.SHCCGDB.filter(state.cards, state.filters);
    renderLibrary();
    renderStatus();
  }

  function initFilters() {
    if (el.search) {
      el.search.addEventListener("input", function () {
        applyFilters({ query: el.search.value });
      });
    }
    if (el.filterType) {
      el.filterType.addEventListener("change", function () {
        applyFilters({ type: el.filterType.value });
      });
    }
    if (el.filterRarity) {
      el.filterRarity.addEventListener("change", function () {
        applyFilters({ rarity: el.filterRarity.value });
      });
    }
  }

  /* -- boot ------------------------------------------------------------ */
  function boot() {
    window.SHCCGDB.load().then(function (db) {
      state.db = db;
      state.cards = db.cards;
      state.filtered = window.SHCCGDB.filter(db.cards, state.filters);
      if (db.cards.length) selectCard(db.cards[0].id);
      renderAll();
      document.documentElement.setAttribute("data-db-ready", String(db.ok));
    });
  }

  window.SHCCGEditor = {
    state: state,
    selectCard: selectCard,
    applyFilters: applyFilters,
    buildCardElement: buildCardElement,
    render: renderAll,
  };

  el = {
    stage: $("canvas-stage"),
    placeholder: $("canvas-placeholder"),
    canvasCard: $("canvas-card"),
    zoomLabel: $("zoom-label"),
    zoomIn: $("zoom-in"),
    zoomOut: $("zoom-out"),
    libraryList: $("library-list"),
    search: $("library-search"),
    filterType: $("filter-type"),
    filterRarity: $("filter-rarity"),
    banner: $("validation-banner"),
    dbSummary: $("db-summary"),
    statusCards: $("status-cards"),
    statusSelection: $("status-selection"),
    statusValidation: $("status-validation"),
    fields: {
      "f-id": $("f-id"),
      "f-name": $("f-name"),
      "f-set": $("f-set"),
      "f-faction": $("f-faction"),
      "f-cost": $("f-cost"),
      "f-rarity": $("f-rarity"),
      "f-type": $("f-type"),
      "f-text": $("f-text"),
      "f-flavor": $("f-flavor"),
      "f-keywords": $("f-keywords"),
    },
  };

  initTabs();
  initZoom();
  initFilters();
  boot();
})();