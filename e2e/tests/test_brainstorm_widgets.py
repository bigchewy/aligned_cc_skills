"""Structural and lint tests for the brainstorming interactive-widgets sidecar."""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "skills/brainstorming/references/templates"
WIDGETS_PARTIAL = REPO_ROOT / "skills/brainstorming/references/widgets.html"
CANONICAL_TEMPLATE_NAMES = [
    "software-template.html",
    "authoring-template.html",
    "roadmap-template.html",
]
TEMPLATE_NAMES = CANONICAL_TEMPLATE_NAMES + [
    "authoring-analysis-template.html",
    "authoring-decision-template.html",
    "authoring-plan-template.html",
]


def test_widgets_partial_exists():
    assert WIDGETS_PARTIAL.exists(), (
        f"widgets sidecar partial must exist at {WIDGETS_PARTIAL.relative_to(REPO_ROOT)}"
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
    # Both guards must early-return before touching the table. The guard may be
    # expressed inline (`if (!document.getElementById(...)) return`) or via a
    # captured variable (`var x = document.getElementById(...); if (!x) return`).
    inline = r"if\s*\(\s*!\s*document\.getElementById\(\s*['\"]{name}['\"]\s*\)\s*\)\s*return"
    captured = (
        r"var\s+(\w+)\s*=\s*document\.getElementById\(\s*['\"]{name}['\"]\s*\)\s*;"
        r"\s*if\s*\(\s*!\s*\1\s*\)\s*return"
    )
    for table_id, label in [("decisions-table", "decision-log"), ("questions-table", "open-questions")]:
        assert re.search(inline.format(name=table_id), text) or re.search(
            captured.format(name=table_id), text
        ), (
            f"{label} widget missing early-return guard for `{table_id}` "
            f"(neither inline nor captured-variable form found)"
        )


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


# Reference regex modeling the documented strip rule's intent. The actual strip
# in production is performed by an LLM agent following `shared-rules.md`'s
# natural-language instruction — there is no runtime regex. This test validates
# the STRUCTURAL CONTRACT that makes any reasonable strip implementation safe:
# the widget <script> block lives OUTSIDE the LIVE-REFRESH delimiters, so any
# strip that targets LIVE-REFRESH (by regex, by AST walk, or by human edit)
# necessarily preserves the widget JS.
STRIP_RE = re.compile(
    r"<!--\s*LIVE-REFRESH-START\s*-->.*?<!--\s*LIVE-REFRESH-END\s*-->",
    re.DOTALL,
)


def _strip_live_refresh(html: str) -> str:
    """Reference implementation of the LIVE-REFRESH strip — used only by this
    structural-contract test, not by the production code path."""
    return STRIP_RE.sub("", html)


def test_widget_script_block_is_structurally_outside_live_refresh():
    """STRUCTURAL CONTRACT: the widget <script> block must live outside the
    LIVE-REFRESH delimiters. Build a fixture that mirrors a real injected page
    (template + sidecar SCRIPT block + a decisions-table) and verify that
    stripping the LIVE-REFRESH range (by any implementation that uses those
    delimiters as anchors) leaves the widget block intact.

    This is NOT a claim that the production strip uses this exact regex — the
    production strip is performed by an LLM agent following shared-rules.md.
    The test asserts the structural property that ANY anchor-honoring strip
    implementation (regex, AST, human edit) preserves widget JS."""
    template = (TEMPLATES_DIR / "software-template.html").read_text()
    widgets = WIDGETS_PARTIAL.read_text()

    # Extract the WIDGETS-SCRIPT block from the sidecar.
    script_match = re.search(
        r"<!-- WIDGETS-SCRIPT-START -->.*?<!-- WIDGETS-SCRIPT-END -->",
        widgets,
        re.DOTALL,
    )
    assert script_match, "widgets.html must contain a WIDGETS-SCRIPT block"
    widget_script = script_match.group(0)

    # Build a fixture: template with widget script injected before </body>, plus a
    # decisions-table somewhere in the body so the bind would succeed at runtime.
    table_html = (
        '<table id="decisions-table"><tbody>'
        '<tr data-id="1" data-title="x"><td><select class="dropdown" data-id="1">'
        '<option value="approve">Approve</option><option value="reject">Reject</option>'
        '</select></td></tr></tbody></table>'
        '<textarea id="decisions-prompt" class="prompt-textarea"></textarea>'
        '<button id="copy-decisions" class="btn"></button>'
        '<button id="regenerate-decisions" class="btn"></button>'
    )
    fixture = template.replace(
        "</body>", table_html + "\n" + widget_script + "\n</body>"
    )

    # Pre-condition: both delimiter pairs present in the fixture.
    assert "<!-- LIVE-REFRESH-START -->" in fixture
    assert "<!-- WIDGETS-SCRIPT-START -->" in fixture

    # Pre-condition: the WIDGETS-SCRIPT range does not overlap the LIVE-REFRESH
    # range. (This is the structural contract — proven by index comparison.)
    lr_start = fixture.index("<!-- LIVE-REFRESH-START -->")
    lr_end = fixture.index("<!-- LIVE-REFRESH-END -->")
    ws_start = fixture.index("<!-- WIDGETS-SCRIPT-START -->")
    ws_end = fixture.index("<!-- WIDGETS-SCRIPT-END -->")
    assert not (lr_start <= ws_start <= lr_end) and not (lr_start <= ws_end <= lr_end), (
        "WIDGETS-SCRIPT block is structurally inside LIVE-REFRESH range — "
        "any strip that targets LIVE-REFRESH delimiters will destroy widget JS"
    )

    # Apply the reference strip and verify the structural property: widget JS
    # survives because it lives outside the targeted range.
    stripped = _strip_live_refresh(fixture)
    assert "<!-- LIVE-REFRESH-START -->" not in stripped
    assert "<!-- LIVE-REFRESH-END -->" not in stripped
    assert "<!-- WIDGETS-SCRIPT-START -->" in stripped, (
        "anchor-based LIVE-REFRESH strip removed the widget JS block — the "
        "WIDGETS-SCRIPT block must be injected outside LIVE-REFRESH delimiters"
    )
    assert "<!-- WIDGETS-SCRIPT-END -->" in stripped
    assert 'id="decisions-table"' in stripped
    assert "decisionLogWidget" in stripped or "decisions-table" in stripped
