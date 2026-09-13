# AGENTS.md — Street Hustle CCG Card Editor

Instructions for any coding agent (Claude Code, Codex, OpenCode, Hermes subagents) working in this repo. Read this before starting any task.

## How work flows here

This repo uses the **issue → PR → CI → merge** loop.

1. **Pick an issue** — find an open issue to work on (or create one for the task).
2. **Branch** — `feat/<slug>` or `fix/<slug>` off latest `main`. One issue per branch.
3. **Read `docs/BUILD_INSTRUCTIONS.md`** — it's the authoritative spec: features, design system (CSS variables), card schema, export formats.
4. **Implement the smallest complete change** — every line must trace to the issue. No drive-by cleanup.
5. **Add/update tests** — a regression test must demonstrably FAIL on pre-fix code, then pass with the fix.
6. **Validate locally** — `python3 scripts/validate_db.py` and any test suite, then push.
7. **Open the PR** — link the issue in the body (e.g. `Closes #N`), summarize approach / tests / risk.
8. **Shepherd CI honestly** — watch `gh pr checks`; fix failures you introduced; never claim "green" without live evidence.
9. **Merge** — when CI is green and the diff is clean, squash-merge and delete the branch.

## Single source of truth

- **`data/STREETHUSTLE_MASTER_DB_v9.6.json`** — the canonical 116-card database. Do NOT hand-edit; drive changes through the editor or an explicit, tested data migration.
- Per-type DBs (`STREETHUSTLE_DEALERS/STASH/ACTIONS/BOROUGHS_DB_v9.6.json`) are derived views — keep their union consistent with the master (26 + 29 + 35 + 26 = 116).
- **`docs/webpages/cards.html`** — current print template: CSS variables, card structure, 5 sheets × 9 cards.
- **`docs/webpages/index.html`** — marketing design system (colors, fonts, noise, scanlines).

## Data schema (validated in CI)

Card object must have: `id`(string), `name`(string), `type`(enum: dealer|stash|action|borough), `rarity`(enum: common|uncommon|rare|legendary), `faction`, `set`, `cost`/`atk`/`def`/`hp`(int), `keywords`(array), `text`, `flavor`, `art_prompt`, `emoji`. See README for the full table.

## Conventions

- **Conventional commits:** `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `ci:`, `chore:`, `perf:`.
- Branch naming: `feat/...`, `fix/...`.
- Keep the design system tokens centralized (CSS variables in `:root`).
- Tests live under `tests/` once the app scaffold exists.

## CI

`.github/workflows/ci.yml` runs `scripts/validate_db.py` (JSON validity, card count = 116, full schema check). Keep it green.

## Non-goals

- Don't modify the canonical game data unless the task explicitly calls for it.
- No drive-by refactors or unrelated formatting churn in a feature PR.