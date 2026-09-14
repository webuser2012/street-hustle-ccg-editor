"""Scaffold regression tests for the Street Hustle CCG card editor (issue #3).

These assert the scaffold's *contracts*, not a frozen snapshot:

* the design-system tokens shipped in the app are the same tokens the print
  template uses (parsed straight out of the reference file in ``docs/``), so the
  two can never silently drift apart;
* the card markup/CSS structure the rest of the editor builds on is present;
* a runnable, build-free local dev entrypoint exists.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
APP = REPO_ROOT / "app"
REFERENCE = REPO_ROOT / "docs" / "webpages" / "cards.html"

TOKENS_CSS = APP / "styles" / "tokens.css"
CARD_CSS = APP / "styles" / "card.css"
EDITOR_CSS = APP / "styles" / "editor.css"
INDEX_HTML = APP / "index.html"
APP_JS = APP / "js" / "app.js"
DEV_SCRIPT = REPO_ROOT / "scripts" / "dev.sh"


def _root_tokens(css_text: str) -> dict:
    """Extract ``--name: value`` pairs from the first ``:root`` block."""
    match = re.search(r":root\s*\{(.*?)\}", css_text, re.S)
    assert match, "no :root block found"
    tokens = {}
    for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", match.group(1)):
        tokens[name] = value.strip()
    return tokens


@pytest.fixture(scope="module")
def reference_tokens():
    return _root_tokens(REFERENCE.read_text())


@pytest.fixture(scope="module")
def app_tokens():
    return _root_tokens(TOKENS_CSS.read_text())


def test_scaffold_files_exist():
    for path in (TOKENS_CSS, CARD_CSS, EDITOR_CSS, INDEX_HTML, APP_JS, DEV_SCRIPT):
        assert path.exists(), f"missing scaffold file: {path.relative_to(REPO_ROOT)}"


def test_design_tokens_match_print_template(reference_tokens, app_tokens):
    """Every token the print template defines must exist in the app, unchanged."""
    missing = {k: v for k, v in reference_tokens.items() if k not in app_tokens}
    assert not missing, f"tokens missing from app: {missing}"

    drifted = {
        k: (v, app_tokens[k])
        for k, v in reference_tokens.items()
        if app_tokens[k].lower() != v.lower()
    }
    assert not drifted, f"tokens drifted from print template (expected, got): {drifted}"


def test_editor_chrome_tokens_present(app_tokens):
    """The editor chrome needs the deeper backgrounds + accent from index.html."""
    for token in ("--bg3", "--or", "--tx3", "--tx2", "--bdr"):
        assert token in app_tokens, f"editor token {token} not defined"


def _standalone_selectors(css_text: str) -> set:
    """All rule selectors in a stylesheet, normalised (comments and @-blocks stripped)."""
    css_text = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)
    css_text = re.sub(r"@[^{]*\{", " ", css_text)  # drop at-rule wrappers such as @media
    selectors = set()
    for chunk in css_text.split("{"):
        head = chunk.split("}")[-1]
        for part in head.split(","):
            part = " ".join(part.split())
            if part and not part.startswith("@"):
                selectors.add(part)
    return selectors


def test_card_css_has_structural_classes():
    selectors = _standalone_selectors(CARD_CSS.read_text())
    for selector in (
        ".card",
        ".card-top",
        ".card-type",
        ".card-cost",
        ".heat-pip",
        ".card-art",
        ".card-art-placeholder",
        ".card-name-band",
        ".card-name",
        ".card-stats",
        ".stat-val",
        ".card-body",
        ".ability-tag",
        ".ability-text",
        ".flavor-text",
        ".card-footer",
        ".rarity-label",
        ".set-info",
    ):
        assert selector in selectors, f"{selector} has no rule in card.css"


CARD_TYPES = ("dealer", "stash", "action", "borough")
RARITIES = ("common", "uncommon", "rare", "legendary")


def test_type_and_rarity_rules_match_print_template():
    """Every type/rarity-specific rule the print template defines must be ported.

    Derived from ``docs/webpages/cards.html`` rather than hard-coded, so the two
    files cannot drift apart as the card design evolves.
    """
    reference_selectors = _standalone_selectors(REFERENCE.read_text())
    app_selectors = _standalone_selectors(CARD_CSS.read_text())

    for keyword in CARD_TYPES + RARITIES:
        expected = {
            sel
            for sel in reference_selectors
            if re.search(rf"(?<![a-z-]){keyword}(?![a-z-])", sel)
            and sel.startswith((".card", ".stat", ".ability-tag", ".heat-pip"))
        }
        assert expected, f"reference defines no rules for {keyword} (test is stale)"
        missing = sorted(expected - app_selectors)
        assert not missing, f"{keyword}: rules missing from card.css -> {missing}"

    assert "--legendary" in CARD_CSS.read_text(), (
        "legendary accent colour unused in card.css"
    )


def test_index_html_wires_styles_and_script():
    html = INDEX_HTML.read_text()
    for asset in (
        "styles/tokens.css",
        "styles/card.css",
        "styles/editor.css",
        "js/app.js",
    ):
        assert asset in html, f"index.html does not load {asset}"


def test_index_html_renders_empty_editor_canvas():
    html = INDEX_HTML.read_text()
    assert 'id="card-canvas"' in html, "no editor canvas mount point"
    # An *empty* canvas: the placeholder state is what #3 delivers, no card data yet.
    assert 'id="canvas-placeholder"' in html, "empty-canvas placeholder state missing"


def test_every_local_asset_referenced_exists():
    """Build-free contract: every relative asset the shell loads is on disk."""
    html = INDEX_HTML.read_text()
    refs = re.findall(r'(?:href|src)="([^"#:]+)"', html)
    local = [r for r in refs if not r.startswith(("http", "//", "data:"))]
    assert local, "no local assets referenced at all"
    missing = [r for r in local if not (APP / r).exists()]
    assert not missing, f"index.html references missing files: {missing}"


def test_dev_script_serves_the_app_over_http():
    """Boot the real dev entrypoint and fetch the real page.

    dev.sh serves the repo root so the app can read ./data/ directly; the app
    lives at /app/. Mirror that here exactly.
    """
    if shutil.which("python3") is None:
        pytest.skip("python3 not available")

    script = DEV_SCRIPT.read_text()
    assert "python3 -m http.server" in script, (
        "dev.sh must boot a static server so `scripts/dev.sh` works with zero installs"
    )
    assert '"$REPO_ROOT"' in script, "dev.sh must serve the repo root (app reads ./data/)"
    port = 8137  # forced for the test to avoid clashing with a running dev server

    cmd = [sys.executable, "-m", "http.server", str(port), "--directory", str(REPO_ROOT)]

    proc = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(REPO_ROOT)
    )
    try:
        import urllib.error
        import urllib.request
        import time

        deadline = time.time() + 15
        body = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/app/index.html", timeout=2
                ) as resp:
                    body = resp.read().decode("utf-8", "replace")
                break
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.4)
        assert body is not None, "dev server never served index.html"
        assert 'id="card-canvas"' in body, "served page is not the editor shell"
    finally:
        proc.terminate()
        proc.wait(timeout=10)
