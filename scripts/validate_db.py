#!/usr/bin/env python3
"""Validate Street Hustle CCG card data: JSON validity, card counts, and schema.

Exit code 0 on success, 1 on any failure. Designed to run in CI and locally
(agents: run `python3 scripts/validate_db.py` before opening a PR).

Schema is TYPE-DEPENDENT. All cards share common fields; each type adds its
own stat block (verified against the canonical v9.6 master DB):

  Common (every card): id, name, type, rarity, set, cost, keywords,
                       emoji, flavor, text, art_prompt
  dealer :  + faction (str), + int atk, def, hp   (26 cards)
  stash  :  + atkBonus (int), + drug (str)        (29 cards)
  action :  + effect (str)                        (35 cards)
  borough:  + heatGain (int or 0)                 (26 cards)

The validation rules live in `validate_cards()` / `validate_data_dir()` so the
editor app and test suite can reuse them without going through the CLI.

Usage:
    python3 scripts/validate_db.py [--data-dir PATH]
"""
import argparse
import json
import pathlib
import sys

EXPECTED_TOTAL = 116
CARD_TYPES = {"dealer", "stash", "action", "borough"}
RARITIES = {"common", "uncommon", "rare", "legendary"}
# Fields required on every card regardless of type.
COMMON_FIELDS = [
    "id", "name", "type", "rarity", "set", "cost", "keywords",
    "emoji", "flavor", "text", "art_prompt",
]
# Per-type extra fields: (field, expected_python_type)
TYPE_FIELDS = {
    "dealer": [("faction", str), ("atk", int), ("def", int), ("hp", int)],
    "stash": [("atkBonus", int), ("drug", str)],
    "action": [("effect", str)],
    "borough": [("heatGain", (int, type(None)))],  # may be absent or 0
}
PER_TYPE_FILES = {
    "DEALERS": 26,
    "STASH": 29,
    "ACTIONS": 35,
    "BOROUGHS": 26,
}
PER_TYPE_NAME = {
    "DEALERS": "dealer", "STASH": "stash",
    "ACTIONS": "action", "BOROUGHS": "borough",
}


def load_json(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _type_name(expected) -> str:
    """Human-readable type name; handles the (int, NoneType) tuple case."""
    if isinstance(expected, tuple):
        return " or ".join(t.__name__ for t in expected)
    return expected.__name__


def _validate_card(card: dict, errors: list, card_index: int) -> None:
    for field in COMMON_FIELDS:
        if field not in card:
            errors.append(f"[{card_index}] missing common field: {field}")

    ctype = card.get("type")
    if ctype is None:
        errors.append(f"[{card_index}] missing type")
        return  # can't check type-specific fields
    if ctype not in CARD_TYPES:
        errors.append(f"[{card_index}] invalid type: {ctype!r}")
        return

    rar = card.get("rarity")
    if rar not in RARITIES:
        errors.append(f"[{card_index}] invalid rarity: {rar!r}")

    kw = card.get("keywords")
    if kw is not None and not isinstance(kw, list):
        errors.append(f"[{card_index}] keywords not a list")

    for field, expected in TYPE_FIELDS.get(ctype, []):
        if field not in card:
            errors.append(f"[{card_index}] {ctype} missing field: {field}")
        elif not isinstance(card.get(field), expected):
            errors.append(
                f"[{card_index}] {ctype}.{field} wrong type: "
                f"{card.get(field)!r} (expected {_type_name(expected)})"
            )


def describe_card_types(cards):
    """Return dict of type -> set of card names across a list of cards."""
    out = {}
    for card in cards:
        if isinstance(card, dict):
            out.setdefault(card.get("type"), set()).add(card.get("name"))
    return out


def validate_cards(cards, declared_total=EXPECTED_TOTAL):
    """Validate an iterable of card dicts (the master set).

    Returns a list of error strings (empty == valid). Pure and importable so
    the editor and tests can reuse it without the CLI/filesystem.
    """
    errors = []
    cards = list(cards)

    if declared_total != EXPECTED_TOTAL:
        errors.append(
            f"declared total_cards = {declared_total}, expected {EXPECTED_TOTAL}"
        )
    if len(cards) != EXPECTED_TOTAL:
        errors.append(
            f"master DB has {len(cards)} cards, expected {EXPECTED_TOTAL}"
        )

    seen_ids, seen_names = set(), set()
    for idx, card in enumerate(cards):
        if not isinstance(card, dict):
            errors.append(f"[{idx}] card is not an object")
            continue
        _validate_card(card, errors, idx)
        cid = card.get("id")
        if cid in seen_ids:
            errors.append(f"duplicate card id: {cid}")
        elif cid:
            seen_ids.add(cid)
        name = card.get("name")
        if name in seen_names:
            errors.append(f"duplicate card name: {name}")
        elif name:
            seen_names.add(name)

    return errors


def validate_data_dir(data_dir):
    """Validate everything under a data directory.

    Returns a list of error strings (empty == valid). Checks JSON validity,
    master counts/schema, per-type counts, and that per-type memberships
    match the master's type assignment.
    """
    data_dir = pathlib.Path(data_dir)
    errors = []

    master_path = data_dir / "STREETHUSTLE_MASTER_DB_v9.6.json"
    if not master_path.exists():
        errors.append(f"FAIL: master DB not found at {master_path}")
        return errors

    try:
        master = load_json(master_path)
    except json.JSONDecodeError as exc:
        errors.append(f"FAIL: {master_path} is not valid JSON: {exc}")
        return errors

    cards = master.get("cards", [])
    errors.extend(
        validate_cards(cards, declared_total=master.get("total_cards"))
    )

    master_by_type = describe_card_types(cards)

    for fname, expected in PER_TYPE_FILES.items():
        fpath = data_dir / f"STREETHUSTLE_{fname}_DB_v9.6.json"
        if not fpath.exists():
            errors.append(f"missing per-type DB: {fname}")
            continue
        try:
            db = load_json(fpath)
        except json.JSONDecodeError as exc:
            errors.append(f"{fname} not valid JSON: {exc}")
            continue
        n = len(db.get("cards", db))
        if n != expected:
            errors.append(f"{fname} has {n} cards, expected {expected}")

        tname = PER_TYPE_NAME[fname]
        subset = {card.get("name") for card in db.get("cards", db)}
        master_names = master_by_type.get(tname, set())
        if subset - master_names:
            errors.append(
                f"{fname} has names not typed '{tname}' in master: "
                f"{sorted(subset - master_names)[:5]}"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data", help="Path to data dir")
    args = parser.parse_args()

    errors = validate_data_dir(args.data_dir)
    if errors:
        print(f"FAIL: {len(errors)} validation error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        f"OK: {EXPECTED_TOTAL} cards validated. Type counts: "
        f"Dealer {PER_TYPE_FILES['DEALERS']}, Stash {PER_TYPE_FILES['STASH']}, "
        f"Action {PER_TYPE_FILES['ACTIONS']}, Borough {PER_TYPE_FILES['BOROUGHS']} "
        f"(sum {sum(PER_TYPE_FILES.values())}). All pass."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())