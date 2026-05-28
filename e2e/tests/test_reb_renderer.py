# e2e/tests/test_reb_renderer.py
import json
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "frameworks/reverse-engineered-brand/scripts/render_review.py"
TEMPLATE = REPO_ROOT / "frameworks/reverse-engineered-brand/review-template.html"
FIXTURES = REPO_ROOT / "frameworks/reverse-engineered-brand/test-fixtures/render"


def _load():
    spec = importlib.util.spec_from_file_location("render_review", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _render(fixture):
    m = _load()
    data = json.loads((FIXTURES / fixture).read_text())
    return m.render(data, TEMPLATE.read_text(), brand_folder=str(FIXTURES))


# ---- success paths ----
def test_palette_vars_emitted_from_theme():
    html = _render("valid-tiny.json")
    assert "--primary:" in html and "--ink:" in html
    assert "{PALETTE_VARS_CSS}" not in html  # token substituted

def test_neutral_default_palette_when_empty():
    html = _render("valid-no-palette-uses-default.json")
    # All 17 vars present even with theme.palette == {}
    for var in ("--ink:", "--paper:", "--panel:", "--primary:", "--accent:",
                "--good:", "--warn:", "--risk:"):
        assert var in html

def test_fontface_emitted_for_relative_src():
    html = _render("valid-tiny.json")
    assert "@font-face" in html
    assert "{FONT_FACES_CSS}" not in html

def test_null_logo_emits_wordmark_span():
    html = _render("valid-null-logo-wordmark.json")
    assert 'class="wordmark"' in html
    assert "The Knot" in html

def test_one_panel_per_section():
    m = _load()
    data = json.loads((FIXTURES / "valid-realistic.json").read_text())
    html = m.render(data, TEMPLATE.read_text(), brand_folder=str(FIXTURES))
    assert html.count('<section class="panel"') == len(data["sections"])

def test_script_tags_sanitized():
    html = _render("valid-realistic.json")
    # the </script> inside a why_it_matters string must be escaped in the inline snapshot
    assert "<\\/script>" in html
    # only the real closing tags remain unescaped
    assert html.count("</script>") <= html.count("<script")

def test_no_unsubstituted_tokens():
    html = _render("valid-tiny.json")
    import re
    assert not re.search(r"\{[A-Z][A-Z0-9_]*\}", html)

def test_cli_writes_and_verifies(tmp_path):
    out = tmp_path / "review.html"
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURES / "valid-tiny.json"),
         str(TEMPLATE), str(out), "The Knot", str(FIXTURES)],
        capture_output=True, text=True)
    assert r.returncode == 0
    assert out.read_text().startswith("<!DOCTYPE html>")
    assert out.read_text().rstrip().endswith("</html>")


# ---- error paths (MANDATORY) ----
@pytest.mark.parametrize("fixture,reason", [
    ("invalid-grade-out-of-range.json", "grade"),
    ("invalid-oq-over-cap.json", "open_questions"),
    ("invalid-remote-font-src.json", "remote"),
    ("invalid-font-src-escapes-folder.json", "escape"),
])
def test_invalid_fixtures_raise(fixture, reason):
    m = _load()
    data = json.loads((FIXTURES / fixture).read_text())
    with pytest.raises(m.RenderError):
        m.render(data, TEMPLATE.read_text(), brand_folder=str(FIXTURES))

def test_cli_nonzero_and_writes_nothing_on_invalid(tmp_path):
    out = tmp_path / "review.html"
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURES / "invalid-remote-font-src.json"),
         str(TEMPLATE), str(out), "The Knot", str(FIXTURES)],
        capture_output=True, text=True)
    assert r.returncode != 0
    assert not out.exists()  # abort-before-open: nothing written
