"""Structural and lint tests for the brainstorming interactive-widgets sidecar."""
import hashlib
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "skills/brainstorming/references/templates"
WIDGETS_PARTIAL = REPO_ROOT / "skills/brainstorming/references/widgets.html"
TEMPLATE_NAMES = [
    "software-template.html",
    "business-template.html",
    "authoring-template.html",
    "planning-template.html",
]


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def test_widgets_partial_exists():
    assert WIDGETS_PARTIAL.exists(), (
        f"widgets sidecar partial must exist at {WIDGETS_PARTIAL.relative_to(REPO_ROOT)}"
    )


def test_template_md5_equality():
    hashes = {name: _md5(TEMPLATES_DIR / name) for name in TEMPLATE_NAMES}
    distinct = set(hashes.values())
    assert len(distinct) == 1, (
        f"all four mode templates must share a single md5; got {hashes}"
    )


def test_widgets_partial_has_required_block_markers():
    text = WIDGETS_PARTIAL.read_text()
    for marker in [
        "<!-- WIDGETS-CSS-START -->",
        "<!-- WIDGETS-CSS-END -->",
        "<!-- WIDGETS-SCRIPT-START -->",
        "<!-- WIDGETS-SCRIPT-END -->",
        "<!-- WIDGET-HTML: decision-log-flat -->",
        "<!-- WIDGET-HTML: decision-log-categorized -->",
        "<!-- WIDGET-HTML: open-questions-flat -->",
        "<!-- WIDGET-HTML: open-questions-categorized -->",
        "<!-- WIDGET-HTML: prompt-box -->",
    ]:
        assert marker in text, f"widgets.html missing marker: {marker}"


def test_widget_selector_lint_no_bare_tbody_tr():
    """Mockup bug regression: widgets must never use `tbody tr` without `[data-id]`
    because section-divider rows lack a <select> and break querySelector chains."""
    text = WIDGETS_PARTIAL.read_text()
    bare = re.findall(r"querySelectorAll\(\s*['\"]tbody tr['\"]\s*\)", text)
    assert not bare, (
        "widgets.html uses bare `querySelectorAll('tbody tr')`; must scope to "
        "`tbody tr[data-id]` to skip section-divider rows"
    )


def test_widget_isolation_guards_present():
    """Each widget IIFE must guard with an early return so a page with only one
    widget table (no Decision Log OR no Open Questions) still loads cleanly."""
    text = WIDGETS_PARTIAL.read_text()
    assert "getElementById('decisions-table')" in text, (
        "missing decisions-table existence check"
    )
    assert "getElementById('questions-table')" in text, (
        "missing questions-table existence check"
    )
    # Both guards must early-return before touching the table
    assert re.search(
        r"if\s*\(\s*!\s*document\.getElementById\(\s*['\"]decisions-table['\"]\s*\)\s*\)\s*return",
        text,
    ), "decision-log widget missing `if (!document.getElementById('decisions-table')) return;` guard"
    assert re.search(
        r"if\s*\(\s*!\s*document\.getElementById\(\s*['\"]questions-table['\"]\s*\)\s*\)\s*return",
        text,
    ), "open-questions widget missing `if (!document.getElementById('questions-table')) return;` guard"


def test_widget_empty_tbody_renders_hint():
    """A widget with zero `tr[data-id]` rows must show a 'no entries' hint, not a
    false 'all approved' message."""
    text = WIDGETS_PARTIAL.read_text()
    # The hint copy is present somewhere in the script (we don't pin exact wording,
    # just that the empty-tbody branch exists)
    assert "No decisions" in text or "no decisions captured" in text.lower(), (
        "decision-log widget missing empty-tbody hint text"
    )
    assert "No open questions" in text or "no open questions" in text.lower(), (
        "open-questions widget missing empty-tbody hint text"
    )


def test_widget_clipboard_fallback_present():
    """Clipboard helper must handle file:// origins (non-secure context) without
    throwing — required because committed snapshots open at file://."""
    text = WIDGETS_PARTIAL.read_text()
    assert "isSecureContext" in text or "document.execCommand" in text, (
        "widget clipboard helper missing the non-secure-context fallback path"
    )


def test_templates_compose_widget_state():
    """Every template's saveState/restoreState IIFE must capture widget select +
    textarea state under `state.widgets`."""
    for name in TEMPLATE_NAMES:
        text = (TEMPLATES_DIR / name).read_text()
        assert "state.widgets" in text, (
            f"{name} live-refresh IIFE missing widget-state composition (state.widgets)"
        )
        assert "data-widget-state" in text or "select.dropdown[data-id]" in text, (
            f"{name} live-refresh IIFE missing widget-state selector hook"
        )
        # Restore path must dispatch change events so the existing widget JS
        # rebuilds row class + prompt textarea after reload.
        assert "dispatchEvent" in text, (
            f"{name} restoreState missing `dispatchEvent(new Event('change'))` "
            f"to re-trigger widget refresh after reload"
        )


def test_widget_script_outside_live_refresh_delimiters():
    """The widget WIDGETS-SCRIPT block must not sit inside the LIVE-REFRESH
    delimiters — otherwise the strip-script rule would destroy widgets in
    committed snapshots."""
    text = WIDGETS_PARTIAL.read_text()
    # The sidecar itself must not even contain the LIVE-REFRESH delimiters —
    # they belong only to the template's auto-refresh IIFE.
    assert "<!-- LIVE-REFRESH-START -->" not in text, (
        "widgets.html must not contain LIVE-REFRESH-START — widget JS must live "
        "in a separate <script> block outside the strip-script delimiters"
    )
    assert "<!-- LIVE-REFRESH-END -->" not in text, (
        "widgets.html must not contain LIVE-REFRESH-END"
    )


def test_widget_selects_carry_dropdown_class():
    """Selector contract: every `<select data-id=...>` in widgets.html MUST
    include `dropdown` in its class attribute, otherwise the state-composition
    selector `select.dropdown[data-id]` misses it on save/restore."""
    text = WIDGETS_PARTIAL.read_text()
    # Find every <select ... data-id="..."> opener and verify it carries
    # `class="..."` with a `dropdown` token. A select with data-id but no
    # `dropdown` class would be a contract violation.
    bad = re.findall(
        r"<select(?![^>]*\bclass\s*=\s*['\"][^'\"]*\bdropdown\b)[^>]*\bdata-id\b[^>]*>",
        text,
    )
    assert not bad, (
        "every widget <select data-id=...> must carry `dropdown` in its class "
        "attribute — `q-dropdown` alone is not sufficient. Offenders: "
        + repr(bad[:3])
    )
