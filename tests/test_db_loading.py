"""Tests for loading the master card DB into editor state (issue #4).

Three contracts are pinned here:

1. **The browser validator and the Python validator agree.** The editor must
   surface the *same* schema errors `scripts/validate_db.py` reports, so the
   same fixtures are fed to both and their error codes compared.
2. **`data/` stays the single source of truth.** The app reads the canonical
   files over HTTP; it must not keep a second copy that can drift.
3. **The UI actually exposes the loaded data and the errors** - library
   filters, card selection and the validation banner are wired in the markup.
"""

import contextlib
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
APP = REPO_ROOT / "app"
DATA_DIR = REPO_ROOT / "data"
MASTER = DATA_DIR / "STREETHUSTLE_MASTER_DB_v9.6.json"
INDEX_HTML = APP / "index.html"
DB_JS = APP / "js" / "db.js"
SCHEMA_JS = APP / "js" / "schema.js"
APP_JS = APP / "js" / "app.js"
JS_FIXTURE_RUNNER = Path(__file__).resolve().parent / "js" / "validate_fixture.js"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import validate_db  # noqa: E402  (repo script, imported as a library)

CARD_TYPES = ("dealer", "stash", "action", "borough")
RARITIES = ("common", "uncommon", "rare", "legendary")

# ---------------------------------------------------------------------------
# Cross-language error-code mapping
# ---------------------------------------------------------------------------
_CODE_PATTERNS = [
    (r"^\[(\d+)\] card is not an object$", lambda m: "not_an_object"),
    (
        r"^\[(\d+)\] missing common field: (.+)$",
        lambda m: f"missing_common_field:{m.group(2)}",
    ),
    (r"^\[(\d+)\] missing type$", lambda m: "missing_type"),
    (r"^\[(\d+)\] invalid type: (.*)$", lambda m: f"invalid_type:{_clean(m.group(2))}"),
    (r"^\[(\d+)\] invalid rarity: (.*)$", lambda m: f"invalid_rarity:{_clean(m.group(2))}"),
    (r"^\[(\d+)\] keywords not a list$", lambda m: "keywords_not_list"),
    (
        r"^\[(\d+)\] (\w+) missing field: (.+)$",
        lambda m: f"missing_type_field:{m.group(2)}:{m.group(3)}",
    ),
    (
        r"^\[(\d+)\] (\w+)\.(\w+) wrong type: .*$",
        lambda m: f"wrong_type:{m.group(2)}:{m.group(3)}",
    ),
    (r"^duplicate card id: (.+)$", lambda m: f"duplicate_id:{m.group(1)}"),
    (r"^duplicate card name: (.+)$", lambda m: f"duplicate_name:{m.group(1)}"),
    (r"^master DB has \d+ cards, expected \d+$", lambda m: "card_count"),
    (r"^declared total_cards = .*, expected \d+$", lambda m: "declared_total"),
]


def _clean(raw: str) -> str:
    """Normalise a repr'd value from the Python error message into a code suffix."""
    raw = raw.strip()
    if raw == "None":
        return "undefined"
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1]
    return raw


def python_error_codes(cards, declared_total) -> list:
    """Run the repo validator and express its errors as comparable codes."""
    codes = []
    for message in validate_db.validate_cards(cards, declared_total=declared_total):
        for pattern, build in _CODE_PATTERNS:
            match = re.match(pattern, message)
            if match:
                codes.append(build(match))
                break
        else:  # pragma: no cover - guards against unmapped validator messages
            raise AssertionError(f"unmapped validator message: {message!r}")
    return sorted(codes)


def js_error_codes(fixture_path: Path) -> list:
    node = shutil.which("node")
    assert node, "node is required to run the editor validator (see CI setup-node step)"
    proc = subprocess.run(
        [node, str(JS_FIXTURE_RUNNER), str(fixture_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"node validator failed: {proc.stderr}"
    return sorted(json.loads(proc.stdout)["codes"])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def master_cards():
    payload = json.loads(MASTER.read_text(encoding="utf-8"))
    assert payload["cards"], "master DB is empty"
    return payload


def _write_fixture(tmp_path: Path, name: str, payload: dict) -> Path:
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def fixtures(tmp_path_factory, master_cards):
    """Valid baseline plus one targeted violation per schema rule."""
    tmp = tmp_path_factory.mktemp("fixtures")
    base_cards = json.loads(json.dumps(master_cards["cards"]))
    declared = master_cards["total_cards"]

    def mutate(name, fn_or_list):
        cards = json.loads(json.dumps(base_cards))
        if callable(fn_or_list):
            fn_or_list(cards)
        else:
            cards = fn_or_list
        return _write_fixture(tmp, name, {"total_cards": declared, "cards": cards})

    def drop_field(field):
        return lambda cards: cards[0].pop(field, None)

    def set_field(field, value):
        def apply(cards):
            cards[0][field] = value

        return apply

    def duplicate_field(field):
        def apply(cards):
            for card in cards:
                if card.get("type") == cards[0]["type"]:
                    card[field] = cards[0][field]
                    return

        return apply

    def wrong_type_for(card_type, field, value):
        def apply(cards):
            for card in cards:
                if card.get("type") == card_type:
                    card[field] = value
                    return
            raise AssertionError(f"no {card_type} card in master DB")

        return apply

    out = {
        "valid": _write_fixture(
            tmp, "valid", {"total_cards": declared, "cards": base_cards}
        ),
        "invalid_type": mutate("invalid_type", set_field("type", "wizard")),
        "invalid_rarity": mutate("invalid_rarity", set_field("rarity", "mythic")),
        "missing_common_field": mutate("missing_field", drop_field("flavor")),
        "missing_type": mutate("missing_type", drop_field("type")),
        "keywords_not_list": mutate("keywords", set_field("keywords", "SUPPLY_CHAIN")),
        "dealer_wrong_type": mutate(
            "dealer_wrong_type", wrong_type_for("dealer", "hp", "10")
        ),
        "borough_wrong_type": mutate(
            "borough_wrong_type", wrong_type_for("borough", "heatGain", "lots")
        ),
        "missing_type_field": mutate(
            "missing_type_field",
            lambda cards: [c.pop("atk", None) for c in cards if c.get("type") == "dealer"],
        ),
        "duplicate_id": mutate("duplicate_id", duplicate_field("id")),
        "duplicate_name": mutate("duplicate_name", duplicate_field("name")),
        "short_db": mutate("short_db", base_cards[:-1]),
        "declared_total": _write_fixture(
            tmp, "declared_total", {"total_cards": 115, "cards": base_cards}
        ),
    }
    return out


# ---------------------------------------------------------------------------
# 1. Validator agreement
# ---------------------------------------------------------------------------
def test_real_master_db_is_valid_in_both_validators(master_cards):
    assert (
        validate_db.validate_cards(
            master_cards["cards"], declared_total=master_cards["total_cards"]
        )
        == []
    ), "the canonical master DB must validate cleanly in Python"


def test_data_dir_validates_clean():
    """The whole data dir (master + per-type DBs) passes the repo validator."""
    assert validate_db.validate_data_dir(DATA_DIR) == []


@pytest.mark.parametrize(
    "fixture_name",
    [
        "valid",
        "invalid_type",
        "invalid_rarity",
        "missing_common_field",
        "missing_type",
        "keywords_not_list",
        "dealer_wrong_type",
        "borough_wrong_type",
        "missing_type_field",
        "duplicate_id",
        "duplicate_name",
        "short_db",
        "declared_total",
    ],
)
def test_browser_validator_agrees_with_repo_validator(fixtures, fixture_name):
    payload = json.loads(fixtures[fixture_name].read_text(encoding="utf-8"))
    expected = python_error_codes(payload["cards"], payload["total_cards"])
    actual = js_error_codes(fixtures[fixture_name])
    assert actual == expected, (
        f"{fixture_name}: browser validator disagrees with scripts/validate_db.py\n"
        f"  js     : {actual}\n  python : {expected}"
    )


def test_validator_agreement_check_can_fail(fixtures):
    """Guard against a vacuous comparison: a broken fixture must be detected."""
    payload = json.loads(fixtures["invalid_type"].read_text(encoding="utf-8"))
    broken_expectation = python_error_codes(payload["cards"], payload["total_cards"])
    assert broken_expectation, "fixture with an invalid type produced no error at all"
    # A valid fixture must NOT produce the same codes, or the comparison is meaningless.
    assert js_error_codes(fixtures["valid"]) != broken_expectation


def test_per_type_databases_match_master(master_cards):
    """26 + 29 + 35 + 26 = 116, and each type DB contains exactly the master's names."""
    by_type = validate_db.describe_card_types(master_cards["cards"])
    total = 0
    for db_name, expected_count in validate_db.PER_TYPE_FILES.items():
        path = DATA_DIR / f"STREETHUSTLE_{db_name}_DB_v9.6.json"
        cards = json.loads(path.read_text(encoding="utf-8"))["cards"]
        assert len(cards) == expected_count
        type_name = validate_db.PER_TYPE_NAME[db_name]
        assert {c["name"] for c in cards} == set(by_type[type_name])
        total += len(cards)
    assert total == validate_db.EXPECTED_TOTAL


# ---------------------------------------------------------------------------
# 2. data/ stays canonical
# ---------------------------------------------------------------------------
def test_app_does_not_keep_a_second_copy_of_the_card_db():
    assert not (APP / "data").exists(), (
        "app/ must not hold its own copy of the card DB - it reads data/ over HTTP"
    )
    assert "../data/" in DB_JS.read_text(), "db.js must resolve the canonical data dir"


def test_db_js_references_the_canonical_filenames():
    source = DB_JS.read_text()
    for name in [MASTER.name] + [
        f"STREETHUSTLE_{db}_DB_v9.6.json" for db in validate_db.PER_TYPE_FILES
    ]:
        assert name in source, f"db.js does not load {name}"
        assert (DATA_DIR / name).exists(), f"missing canonical data file {name}"


# ---------------------------------------------------------------------------
# 3. UI wiring
# ---------------------------------------------------------------------------
def test_index_html_loads_the_db_modules():
    html = INDEX_HTML.read_text()
    for asset in ("js/schema.js", "js/db.js", "js/app.js"):
        assert asset in html, f"index.html does not load {asset}"


def test_library_offers_every_type_and_rarity_filter():
    html = INDEX_HTML.read_text()
    type_options = set(re.findall(r'<option value="([a-z]+)"', html))
    assert set(CARD_TYPES).issubset(type_options), "library missing card-type filters"
    assert set(RARITIES).issubset(type_options), "library missing rarity filters"
    assert 'id="library-search"' in html, "library has no search box"


def test_validation_errors_have_a_place_to_surface():
    html = INDEX_HTML.read_text()
    assert 'id="validation-banner"' in html, "no UI surface for schema errors"
    source = APP_JS.read_text()
    assert 'errors' in source and "renderBanner" in source, (
        "app.js does not render the validation errors"
    )


def test_canvas_renders_every_card_type_layout():
    """Each type gets its own stats block, mirroring docs/webpages/cards.html."""
    source = APP_JS.read_text()
    for card_type in CARD_TYPES:
        assert f'"{card_type}"' in source, f"no render branch for {card_type}"
    for marker in ("card-stats", "card-type", "card-name-band", "card-footer"):
        assert marker in source, f"rendered card is missing {marker}"


# ---------------------------------------------------------------------------
# 4. Real HTTP round-trip
# ---------------------------------------------------------------------------
@contextlib.contextmanager
def _serve(root: Path, port: int):
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
            "--directory",
            str(root),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/app/index.html", timeout=2)
                break
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.3)
        else:  # pragma: no cover
            raise AssertionError("server never came up")
        yield f"http://127.0.0.1:{port}"
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_app_can_fetch_everything_it_needs_over_http():
    """Exercise the loader's real fetch paths against a served repo root."""
    with _serve(REPO_ROOT, 8138) as base:
        html = urllib.request.urlopen(f"{base}/app/index.html", timeout=5).read().decode()
        assert 'id="library-list"' in html

        for asset in ("js/schema.js", "js/db.js", "js/app.js"):
            resp = urllib.request.urlopen(f"{base}/app/{asset}", timeout=5)
            assert resp.status == 200, f"{asset} not served"

        payload = json.loads(
            urllib.request.urlopen(
                f"{base}/data/{MASTER.name}", timeout=5
            ).read().decode()
        )
        assert len(payload["cards"]) == validate_db.EXPECTED_TOTAL

        for db_name in validate_db.PER_TYPE_FILES:
            url = f"{base}/data/STREETHUSTLE_{db_name}_DB_v9.6.json"
            assert urllib.request.urlopen(url, timeout=5).status == 200
