/* Street Hustle CCG - client-side card schema validation (issue #4).
 *
 * This is the browser-side mirror of the rules in `scripts/validate_db.py` so
 * the editor can validate the master DB it loads and surface schema errors in
 * the UI without a server. The two implementations are pinned to each other by
 * `tests/test_db_loading.py`, which feeds identical fixtures to both and fails
 * if they disagree - keep the codes and ordering in sync when either changes.
 *
 * Errors are `{code, message}` objects. `code` is the cross-language contract;
 * `message` is human-facing text.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else {
    root.SHCCGSchema = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var EXPECTED_TOTAL = 116;
  var CARD_TYPES = ["dealer", "stash", "action", "borough"];
  var RARITIES = ["common", "uncommon", "rare", "legendary"];
  var COMMON_FIELDS = [
    "id", "name", "type", "rarity", "set", "cost", "keywords",
    "emoji", "flavor", "text", "art_prompt",
  ];
  var TYPE_FIELDS = {
    dealer: { faction: "str", atk: "int", def: "int", hp: "int" },
    stash: { atkBonus: "int", drug: "str" },
    action: { effect: "str" },
    borough: { heatGain: "int_or_null" },
  };
  var PER_TYPE_FILES = { DEALERS: 26, STASH: 29, ACTIONS: 35, BOROUGHS: 26 };
  var PER_TYPE_NAME = {
    DEALERS: "dealer", STASH: "stash", ACTIONS: "action", BOROUGHS: "borough",
  };

  function matchesType(value, expected) {
    switch (expected) {
      case "int":
        return typeof value === "number" && Number.isInteger(value);
      case "int_or_null":
        return value === null || (typeof value === "number" && Number.isInteger(value));
      case "str":
        return typeof value === "string";
      default:
        return false;
    }
  }

  function expectedLabel(expected) {
    return expected === "int_or_null" ? "int" : expected;
  }

  function isPlainObject(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
  }

  function validateCard(card, errors, idx) {
    if (!isPlainObject(card)) {
      errors.push({ code: "not_an_object", message: "[" + idx + "] card is not an object" });
      return;
    }

    COMMON_FIELDS.forEach(function (field) {
      if (!Object.prototype.hasOwnProperty.call(card, field)) {
        errors.push({
          code: "missing_common_field:" + field,
          message: "[" + idx + "] missing common field: " + field,
        });
      }
    });

    var ctype = card.type;
    if (ctype === undefined || ctype === null) {
      errors.push({ code: "missing_type", message: "[" + idx + "] missing type" });
      return;
    }
    if (CARD_TYPES.indexOf(ctype) === -1) {
      errors.push({
        code: "invalid_type:" + ctype,
        message: "[" + idx + "] invalid type: " + JSON.stringify(ctype),
      });
      return;
    }

    if (RARITIES.indexOf(card.rarity) === -1) {
      errors.push({
        code: "invalid_rarity:" + card.rarity,
        message: "[" + idx + "] invalid rarity: " + JSON.stringify(card.rarity),
      });
    }

    var kw = card.keywords;
    if (kw !== undefined && kw !== null && !Array.isArray(kw)) {
      errors.push({ code: "keywords_not_list", message: "[" + idx + "] keywords not a list" });
    }

    var fields = TYPE_FIELDS[ctype] || {};
    Object.keys(fields).forEach(function (field) {
      var expected = fields[field];
      if (!Object.prototype.hasOwnProperty.call(card, field)) {
        errors.push({
          code: "missing_type_field:" + ctype + ":" + field,
          message: "[" + idx + "] " + ctype + " missing field: " + field,
        });
      } else if (!matchesType(card[field], expected)) {
        errors.push({
          code: "wrong_type:" + ctype + ":" + field,
          message:
            "[" + idx + "] " + ctype + "." + field + " wrong type: " +
            JSON.stringify(card[field]) + " (expected " + expectedLabel(expected) + ")",
        });
      }
    });
  }

  /** Validate the master card list. Returns an array of {code, message}. */
  function validateCards(cards, declaredTotal) {
    var errors = [];
    cards = cards || [];

    if (declaredTotal !== EXPECTED_TOTAL) {
      errors.push({
        code: "declared_total",
        message:
          "declared total_cards = " + declaredTotal + ", expected " + EXPECTED_TOTAL,
      });
    }
    if (cards.length !== EXPECTED_TOTAL) {
      errors.push({
        code: "card_count",
        message: "master DB has " + cards.length + " cards, expected " + EXPECTED_TOTAL,
      });
    }

    var seenIds = {};
    var seenNames = {};
    cards.forEach(function (card, idx) {
      if (!isPlainObject(card)) {
        errors.push({ code: "not_an_object", message: "[" + idx + "] card is not an object" });
        return;
      }
      validateCard(card, errors, idx);

      var cid = card.id;
      if (Object.prototype.hasOwnProperty.call(seenIds, cid)) {
        errors.push({ code: "duplicate_id:" + cid, message: "duplicate card id: " + cid });
      } else if (cid) {
        seenIds[cid] = true;
      }

      var name = card.name;
      if (Object.prototype.hasOwnProperty.call(seenNames, name)) {
        errors.push({ code: "duplicate_name:" + name, message: "duplicate card name: " + name });
      } else if (name) {
        seenNames[name] = true;
      }
    });

    return errors;
  }

  /** Card names grouped by type, for per-type membership checks. */
  function describeCardTypes(cards) {
    var out = {};
    (cards || []).forEach(function (card) {
      if (isPlainObject(card)) {
        var t = card.type === undefined ? "undefined" : card.type;
        if (!out[t]) out[t] = [];
        out[t].push(card.name);
      }
    });
    return out;
  }

  /**
   * Validate the per-type databases against the master's type assignment.
   * `perTypeDbs` maps DB name (DEALERS, ...) to its card array (or null when
   * the file is missing/unreadable).
   */
  function validatePerType(masterCards, perTypeDbs, perTypeErrors) {
    var errors = perTypeErrors ? perTypeErrors.slice() : [];
    var masterByType = describeCardTypes(masterCards);

    Object.keys(PER_TYPE_FILES).forEach(function (fname) {
      var expected = PER_TYPE_FILES[fname];
      var cards = (perTypeDbs || {})[fname];
      if (!cards) {
        errors.push({
          code: "missing_per_type_db:" + fname,
          message: "missing per-type DB: " + fname,
        });
        return;
      }
      if (cards.length !== expected) {
        errors.push({
          code: "per_type_count:" + fname,
          message: fname + " has " + cards.length + " cards, expected " + expected,
        });
      }
      var tname = PER_TYPE_NAME[fname];
      var masterNames = masterByType[tname] || [];
      var unmatched = cards
        .map(function (c) { return isPlainObject(c) ? c.name : undefined; })
        .filter(function (name) { return name !== undefined && masterNames.indexOf(name) === -1; });
      if (unmatched.length) {
        errors.push({
          code: "per_type_membership:" + fname,
          message:
            fname + " has names not typed '" + tname + "' in master: " +
            JSON.stringify(unmatched.sort().slice(0, 5)),
        });
      }
    });

    return errors;
  }

  /** Counts the editor shows in the status bar / library filters. */
  function summarize(cards) {
    var byType = {};
    var byRarity = {};
    var bySet = {};
    var keywords = {};
    CARD_TYPES.forEach(function (t) { byType[t] = 0; });
    RARITIES.forEach(function (r) { byRarity[r] = 0; });

    (cards || []).forEach(function (card) {
      if (!isPlainObject(card)) return;
      if (byType[card.type] !== undefined) byType[card.type] += 1;
      if (byRarity[card.rarity] !== undefined) byRarity[card.rarity] += 1;
      if (card.set) bySet[card.set] = (bySet[card.set] || 0) + 1;
      (Array.isArray(card.keywords) ? card.keywords : []).forEach(function (kw) {
        keywords[kw] = (keywords[kw] || 0) + 1;
      });
    });

    return {
      total: (cards || []).length,
      byType: byType,
      byRarity: byRarity,
      bySet: bySet,
      keywords: keywords,
    };
  }

  return {
    EXPECTED_TOTAL: EXPECTED_TOTAL,
    CARD_TYPES: CARD_TYPES,
    RARITIES: RARITIES,
    COMMON_FIELDS: COMMON_FIELDS,
    TYPE_FIELDS: TYPE_FIELDS,
    PER_TYPE_FILES: PER_TYPE_FILES,
    PER_TYPE_NAME: PER_TYPE_NAME,
    validateCard: validateCard,
    validateCards: validateCards,
    validatePerType: validatePerType,
    describeCardTypes: describeCardTypes,
    summarize: summarize,
  };
});