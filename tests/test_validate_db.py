"""Unit tests for scripts/validate_db.py.

Run with:  python3 -m pytest tests/ -q
"""
import json
import pathlib
import tempfile
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import validate_db as v


def base_card(**overrides):
    """Minimal valid dealer card; override fields with kwargs."""
    card = {
        "id": "d_punk",
        "name": "Street Punk",
        "type": "dealer",
        "rarity": "common",
        "set": "SCE",
        "cost": 1,
        "keywords": ["SUPPLY_CHAIN"],
        "emoji": "😤",
        "flavor": "Every empire starts somewhere.",
        "text": "ATK 1, HP 10.",
        "art_prompt": "a card",
        # dealer stat block
        "faction": "STREET_CREW",
        "atk": 1,
        "def": 0,
        "hp": 10,
    }
    card.update(overrides)
    return card


def valid_deck(n=116):
    """A schema-correct set of n cards with the right per-type distribution.

    0-25 dealer, 26-54 stash, 55-89 action, 90-115 borough (mirrors v9.6).
    """
    decks = []
    for i in range(n):
        if i < 26:
            card = base_card(id=f"d_{i:03d}", name=f"Dealer {i:03d}")
        elif i < 55:
            card = base_card(
                id=f"s_{i:03d}", name=f"Stash {i:03d}", type="stash",
                atkBonus=1, drug="weed")
        elif i < 90:
            card = base_card(
                id=f"a_{i:03d}", name=f"Action {i:03d}", type="action",
                effect="draw1")
        else:
            card = base_card(
                id=f"b_{i:03d}", name=f"Borough {i:03d}", type="borough",
                heatGain=1)
        decks.append(card)
    return decks


# --- Pure validator tests (validate_cards) -----------------------------


def test_valid_deck_passes():
    assert v.validate_cards(valid_deck(), declared_total=116) == []


def test_missing_common_field_fails():
    cards = valid_deck()
    del cards[0]["id"]
    errors = v.validate_cards(cards, declared_total=116)
    assert any("missing common field: id" in e for e in errors)


def test_invalid_rarity_fails():
    cards = valid_deck()
    cards[0]["rarity"] = "mythic"
    errors = v.validate_cards(cards, declared_total=116)
    assert any("invalid rarity: 'mythic'" in e for e in errors)


def test_invalid_type_fails():
    cards = valid_deck()
    cards[0]["type"] = "gear"
    errors = v.validate_cards(cards, declared_total=116)
    assert any("invalid type: 'gear'" in e for e in errors)


def test_wrong_total_count_fails():
    cards = valid_deck(n=116)[:100]
    errors = v.validate_cards(cards, declared_total=116)
    assert any("has 100 cards" in e for e in errors)


def test_dealer_missing_atk_fails():
    cards = valid_deck()
    del cards[0]["atk"]
    errors = v.validate_cards(cards, declared_total=116)
    assert any("dealer missing field: atk" in e for e in errors)


def test_duplicate_id_fails():
    cards = valid_deck()
    cards[1]["id"] = cards[0]["id"]
    errors = v.validate_cards(cards, declared_total=116)
    assert any(e.startswith("duplicate card id:") for e in errors)


def test_duplicate_name_fails():
    cards = valid_deck()
    cards[1]["name"] = cards[0]["name"]
    errors = v.validate_cards(cards, declared_total=116)
    assert any(e.startswith("duplicate card name:") for e in errors)


# --- Filesystem-level tests (validate_data_dir) ------------------------


def _write_data_dir(cards, per_type=None):
    tmp = tempfile.mkdtemp()
    master = {"version": "9.6", "total_cards": len(cards), "cards": cards}
    (pathlib.Path(tmp) / "STREETHUSTLE_MASTER_DB_v9.6.json").write_text(
        json.dumps(master)
    )
    for fname, names in (per_type or {}).items():
        (pathlib.Path(tmp) / f"STREETHUSTLE_{fname}_DB_v9.6.json").write_text(
            json.dumps({"cards": [{"name": n} for n in names]})
        )
    return tmp


def test_data_dir_per_type_count_fails():
    cards = valid_deck()
    tmp = _write_data_dir(cards, per_type={
        "DEALERS": [c["name"] for c in cards if c["type"] == "dealer"],
        "STASH": [c["name"] for c in cards if c["type"] == "stash"],
        "ACTIONS": [c["name"] for c in cards if c["type"] == "action"][:34],
        "BOROUGHS": [c["name"] for c in cards if c["type"] == "borough"],
    })
    errors = v.validate_data_dir(tmp)
    assert any("ACTIONS has 34 cards, expected 35" in e for e in errors)


def test_data_dir_missing_master_fails():
    empty = tempfile.mkdtemp()
    errors = v.validate_data_dir(empty)
    assert any("master DB not found" in e for e in errors)