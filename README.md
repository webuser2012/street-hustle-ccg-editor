# Street Hustle CCG — Card Editor

[![CI](https://github.com/webuser2012/street-hustle-ccg-editor/actions/workflows/ci.yml/badge.svg)](https://github.com/webuser2012/street-hustle-ccg-editor/actions/workflows/ci.yml)

A web-based card editor for **Street Hustle CCG** (collectible card game). Build print-ready cards and JSON game data for the engine.

> **Current status:** Repo seeded with canonical game data (116 cards v9.6) and the build instructions. The editor app itself is a work-in-progress — see the [issue tracker](https://github.com/webuser2012/street-hustle-ccg-editor/issues).

## What this repo is

- **`data/`** — Single source of truth: the full 116-card database (`STREETHUSTLE_MASTER_DB_v9.6.json`) plus per-type DBs (Dealer / Stash / Action / Borough). Card totals are validated in CI.
- **`docs/BUILD_INSTRUCTIONS.md`** — Complete spec for building the card editor (features, design system, schema).
- **`docs/webpages/`** — Reference implementation files: the current print template (`cards.html`) and marketing design system (`index.html`).
- **`.github/workflows/`** — CI: validates JSON data and enforces the card schema.

## Card editor feature goals

- **Drag & drop custom artwork** onto each card
- **Design colors** for text, borders, backgrounds per card type/rarity
- **Edit all text fields** (name, stats, abilities, flavor text)
- **Visual identity** by card type (Dealer / Stash / Action / Borough) and rarity
- **Export print-ready cards** (PNG/PDF) and **JSON data** for the game engine
- **Load/save projects** from the master DB (116 cards v9.6)

## Quick start (once the app exists)

```bash
npm install
npm run dev        # local dev server
npm run validate   # validate the card data + schema
npm test           # run the test suite
```

## Data schema (card object)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique card id |
| `name` | string | Card name |
| `type` | enum | `dealer` \| `stash` \| `action` \| `borough` |
| `rarity` | enum | `common` \| `uncommon` \| `rare` \| `legendary` |
| `faction`, `set` | string | Faction and set membership |
| `cost`, `atk`, `def`, `hp` | int | Game stats |
| `keywords` | array | Mechanic keywords |
| `text` | string | Card ability text |
| `flavor` | string | Flavor / lore text |
| `art_prompt` | string | Leonardo.ai art prompt |
| `emoji` | string | Icon |

## Dev workflow (agents)

This repo runs the **issue → PR → CI → merge** loop. See `AGENTS.md` in the repo root for how coding agents (Claude Code, Codex, OpenCode, Hermes subagents) should pick up an issue, implement it on a branch, open a PR, and shepherd CI honestly.

- New feature/bug → open an issue → agent implements → PR auto-validates in CI → merge to `main`.
- `main` is a **protected branch**: PRs must pass CI and get at least one approving review.

## License

MIT © 2026 David Bridges