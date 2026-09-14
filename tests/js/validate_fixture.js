#!/usr/bin/env node
/* Run the editor's browser-side schema validator over a fixture.
 *
 * Usage: node tests/js/validate_fixture.js <fixture.json>
 *
 * The fixture is `{"total_cards": N, "cards": [...]}` - the same shape the
 * master DB has. Prints `{"codes": [...], "count": N}` on stdout so the Python
 * suite can compare this validator's verdict with scripts/validate_db.py.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const schema = require(path.join(__dirname, "..", "..", "app", "js", "schema.js"));

const fixturePath = process.argv[2];
if (!fixturePath) {
  console.error("usage: validate_fixture.js <fixture.json>");
  process.exit(2);
}

const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const errors = schema.validateCards(fixture.cards || [], fixture.total_cards);

process.stdout.write(
  JSON.stringify({
    codes: errors.map((e) => e.code),
    count: errors.length,
  })
);
