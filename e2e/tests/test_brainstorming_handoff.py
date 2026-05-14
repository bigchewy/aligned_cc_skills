"""Authoring → Research sub-flow contract tests.

The Authoring mode dispatches a sub-agent that follows the contract in
`skills/brainstorming/references/research-mini-protocol.md`. The sub-agent
writes its synthesis to a file with three required headings; Authoring's
validation step gates integration on those headings being present.

These tests exercise the validator (a pure-Python translation of the
validation step in modes/authoring.md) against fixture synthesis files.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "e2e/fixtures/brainstorming-handoff"


def validate_synthesis(text: str) -> tuple[bool, list[str]]:
    """Return (ok, errors) — same rules as the validation step in modes/authoring.md.

    The protocol contract accepts either em-dash (preferred) or regular hyphen
    as the separator between the level and the caveat.
    """
    errors = []
    if "## Synthesis" not in text:
        errors.append("missing ## Synthesis heading")
    if "## Open Questions" not in text:
        errors.append("missing ## Open Questions heading")
    if "## Confidence" not in text:
        errors.append("missing ## Confidence heading")
    else:
        idx = text.index("## Confidence")
        body = text[idx + len("## Confidence"):].strip()
        first_line = body.splitlines()[0] if body else ""
        if not any(level in first_line.lower() for level in ("high", "medium", "low")):
            errors.append("## Confidence missing high/medium/low level")
        if "—" not in first_line and "-" not in first_line:
            errors.append("## Confidence missing caveat (separator '—' or '-' required)")
    return (not errors, errors)


def test_well_formed_synthesis_passes_validation():
    fixture = FIXTURES / "research-instrument-review-synthesis-valid.md"
    text = fixture.read_text()
    ok, errors = validate_synthesis(text)
    assert ok, f"valid synthesis fixture failed validation: {errors}"


def test_question_fixture_has_question_and_constraints():
    fixture = FIXTURES / "research-instrument-review-question.md"
    text = fixture.read_text()
    assert "## Question" in text or "Question:" in text, "question file must state question"
    assert "## Constraints" in text or "Constraints:" in text, "question file must state constraints"


def test_synthesis_missing_confidence_heading_fails_validation():
    fixture = FIXTURES / "research-instrument-review-synthesis-missing-confidence.md"
    text = fixture.read_text()
    ok, errors = validate_synthesis(text)
    assert not ok, "synthesis missing ## Confidence should fail validation"
    assert any("Confidence" in e for e in errors), \
        f"expected error to call out missing Confidence; got: {errors}"


def test_synthesis_confidence_without_caveat_fails_validation():
    fixture = FIXTURES / "research-instrument-review-synthesis-no-caveat.md"
    text = fixture.read_text()
    ok, errors = validate_synthesis(text)
    assert not ok, "synthesis Confidence without caveat should fail validation"
    assert any("caveat" in e.lower() for e in errors), \
        f"expected error to call out missing caveat; got: {errors}"


def test_synthesis_empty_file_fails_validation():
    fixture = FIXTURES / "research-instrument-review-synthesis-empty.md"
    text = fixture.read_text()
    ok, errors = validate_synthesis(text)
    assert not ok, "empty synthesis should fail validation"
    # All three required headings missing
    assert len(errors) >= 3, f"expected ≥3 errors from empty synthesis; got: {errors}"


def test_portfolio_fixture_entries_match_schema():
    fixture = FIXTURES / "portfolio-fixture.md"
    text = fixture.read_text()
    # Three entries
    entry_count = text.count("## ") - text.count("##  ")  # crude H2 count
    assert entry_count >= 3, f"expected ≥3 portfolio entries; found {entry_count}"
    # Every required field must appear at least 3 times (one per entry)
    for field in [
        "**Target mode:**",
        "**Status:**",
        "**Rough size:**",
        "**Prerequisites:**",
        "**External dependencies:**",
        "**Why now:**",
        "**Spawn brief (one paragraph, brainstorm-ready):**",
        "**Success criterion:**",
    ]:
        count = text.count(field)
        assert count >= 3, f"field {field} appears {count} times; expected ≥3"


def test_portfolio_entry_with_missing_keywords_signals_disambiguation():
    """Per design §Error paths #4: a spawn-brief paragraph that omits
    mode-disambiguating keywords falls through to 5-way disambiguation —
    not silent mis-routing.

    This is a contract test: the fixture's third entry intentionally
    has a generic spawn brief with no mode-disambiguating verbs ('design',
    'sequence', 'compare', 'roadmap'). The test asserts the brief content
    truly lacks those signals; the runtime test of the router behavior
    is part of the eval scenarios (Task 21).
    """
    fixture = FIXTURES / "portfolio-fixture.md"
    text = fixture.read_text()
    # The third entry is the generic-brief case; find it and check
    # its spawn-brief blockquote does NOT contain mode-disambiguating verbs
    third_marker = "## Generic-brief case"
    assert third_marker in text, (
        f"portfolio fixture missing '{third_marker}' entry — fixture drift would silently disable this contract test"
    )
    third_block_start = text.index(third_marker)
    # Extract the spawn-brief blockquote in the third entry
    spawn_idx = text.index("**Spawn brief", third_block_start)
    quote_start = text.index("> ", spawn_idx)
    quote_end = text.index("\n\n", quote_start)
    quote = text[quote_start:quote_end].lower()
    forbidden = ["design", "sequence", "compare", "roadmap", "research", "literature"]
    found = [k for k in forbidden if k in quote]
    assert not found, \
        f"third entry's spawn brief was supposed to be generic; found mode-disambiguating verbs: {found}"
