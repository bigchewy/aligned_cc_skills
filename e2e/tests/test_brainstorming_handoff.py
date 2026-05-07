"""Authoring → Research sub-flow contract tests.

The Authoring mode dispatches a sub-agent that follows the contract in
`skills/brainstorming/references/research-mini-protocol.md`. The sub-agent
writes its synthesis to a file with three required headings; Authoring's
validation step gates integration on those headings being present.

These tests exercise the validator (a pure-Python translation of the
validation step in modes/authoring.md) against fixture synthesis files.
"""
from pathlib import Path

import pytest

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
