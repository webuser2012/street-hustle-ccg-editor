/* Street Hustle CCG - master DB loader (issue #4).
 *
 * Loads the canonical card data from `data/` into editor state, validates it
 * with the browser-side schema mirror, and exposes filtering for the library.
 * `data/` stays the single source of truth: the editor reads the same files CI
 * validates, it does not keep its own copy.
 */
(function (root) {
  "use strict";

  var schema = root.SHCCGSchema;

  var FILES = {
    master: "STREETHUSTLE_MASTER_DB_v9.6.json",
    perType: {
      DEALERS: "STREETHUSTLE_DEALERS_DB_v9.6.json",
      STASH: "STREETHUSTLE_STASH_DB_v9.6.json",
      ACTIONS: "STREETHUSTLE_ACTIONS_DB_v9.6.json",
      BOROUGHS: "STREETHUSTLE_BOROUGHS_DB_v9.6.json",
    },
  };

  /** Absolute URL of the canonical data directory (app/ lives beside data/). */
  function dataDir() {
    var base = root.document ? root.document.baseURI : "http://localhost/app/index.html";
    return new URL("../data/", base).href;
  }

  function fetchJson(url) {
    return fetch(url).then(function (resp) {
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status + " for " + url);
      }
      return resp.json();
    });
  }

  function fetchCards(url) {
    return fetchJson(url).then(function (json) {
      return Array.isArray(json.cards) ? json.cards : json;
    });
  }

  /**
   * Load + validate everything under `data/`.
   *
   * Never rejects: a broken or unreachable DB resolves to a result whose
   * `errors` array explains what went wrong, so the UI can render it.
   */
  function load() {
    var dir = dataDir();
    var perType = {};
    var errors = [];

    var perTypeJobs = Object.keys(FILES.perType).map(function (name) {
      return fetchCards(dir + FILES.perType[name])
        .then(function (cards) {
          perType[name] = cards;
        })
        .catch(function (err) {
          perType[name] = null;
          errors.push({
            code: "missing_per_type_db:" + name,
            message: "missing per-type DB: " + name + " (" + err.message + ")",
          });
        });
    });

    var masterJob = fetchJson(dir + FILES.master).then(
      function (json) {
        return {
          meta: {
            version: json.version,
            set_name: json.set_name,
            release_date: json.release_date,
            total_cards: json.total_cards,
          },
          cards: Array.isArray(json.cards) ? json.cards : [],
        };
      },
      function (err) {
        errors.push({
          code: "master_fetch_failed",
          message: "could not load master DB: " + err.message,
        });
        return { meta: {}, cards: [] };
      }
    );

    return Promise.all(perTypeJobs.concat([masterJob])).then(function (results) {
      var master = results[results.length - 1];
      var cardErrors = schema.validateCards(master.cards, master.meta.total_cards);
      var allErrors = errors.concat(cardErrors).concat(
        schema.validatePerType(master.cards, perType, [])
      );

      var byId = {};
      master.cards.forEach(function (card) {
        if (card && card.id) byId[card.id] = card;
      });

      return {
        ok: allErrors.length === 0,
        cards: master.cards,
        byId: byId,
        perType: perType,
        errors: allErrors,
        stats: schema.summarize(master.cards),
        meta: master.meta,
      };
    });
  }

  /** Case-insensitive filter over the loaded card list. */
  function filter(cards, filters) {
    filters = filters || {};
    var type = filters.type && filters.type !== "all" ? filters.type : null;
    var rarity = filters.rarity && filters.rarity !== "all" ? filters.rarity : null;
    var q = (filters.query || "").trim().toLowerCase();

    return (cards || []).filter(function (card) {
      if (type && card.type !== type) return false;
      if (rarity && card.rarity !== rarity) return false;
      if (!q) return true;
      return haystack(card).indexOf(q) !== -1;
    });
  }

  function haystack(card) {
    var parts = [
      card.name, card.id, card.type, card.rarity, card.set, card.faction,
      card.drug, card.text, card.effect, card.flavor,
    ].concat(
      Array.isArray(card.keywords) ? card.keywords : [],
      Array.isArray(card.art_prompt) ? card.art_prompt : [card.art_prompt]
    );
    return parts
      .filter(function (p) { return typeof p === "string"; })
      .join(" ")
      .toLowerCase();
  }

  root.SHCCGDB = {
    FILES: FILES,
    dataDir: dataDir,
    load: load,
    filter: filter,
    haystack: haystack,
  };
})(typeof globalThis !== "undefined" ? globalThis : this);