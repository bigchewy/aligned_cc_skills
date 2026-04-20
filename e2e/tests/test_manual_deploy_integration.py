"""Structural fixture-driven test for the manual-deploy Post-Automation
section shape. Validates the expected post-scan plan layout — the mechanical
contract the writing-plans scan step is expected to produce, and the shape
Step 0.5 relies on for parsing. Does not invoke the LLM; behavioral coverage
lives in the promptfoo eval scenarios under e2e/scenarios/manual-deploy/."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).resolve().parent.parent
FIXTURES = E2E_DIR / "fixtures" / "manual-deploy"


def _read(relative: str) -> str:
    return (FIXTURES / relative).read_text(encoding="utf-8")


def test_active_plan_before_scan_has_no_post_automation_section():
    text = _read("plans/active-plan-before-scan.md")
    assert "## Manual Steps (Post-Automation)" not in text, (
        "Before-scan fixture must not have a Post-Automation section"
    )


def test_active_plan_after_scan_has_post_automation_section():
    text = _read("plans/active-plan-after-scan.md")
    assert "## Manual Steps (Post-Automation)" in text
    assert "### M1 migrations" in text
    assert "supabase/migrations/022_add_tos_version.sql" in text
    assert "[evidence pending]" in text


def test_active_plan_after_scan_injects_exemption_html_comment():
    text = _read("plans/active-plan-after-scan.md")
    # The comment must precede the Post-Automation heading
    comment_idx = text.find("To exempt a file from the manual-deploy gate")
    heading_idx = text.find("## Manual Steps (Post-Automation)")
    assert comment_idx != -1, "Exemption HTML comment must be present"
    assert comment_idx < heading_idx, (
        "Exemption HTML comment must appear before the Post-Automation heading"
    )


def test_plan_with_evidence_complete_parses_as_valid():
    text = _read("plans/plan-with-evidence-complete.md")
    m1_idx = text.find("### M1 migrations")
    assert m1_idx != -1
    # Evidence sub-bullet must be a SQL Editor URL matching M1's regex kind (a)
    url_re = re.compile(
        r"https://supabase\.com/dashboard/project/[a-z0-9]+/sql/[0-9a-f-]+"
    )
    assert url_re.search(text[m1_idx:]), (
        "plan-with-evidence-complete must have an M1 sub-bullet matching the "
        "SQL Editor URL regex"
    )


def test_plan_with_exemption_declares_built_in_token():
    text = _read("plans/plan-with-exemption.md")
    assert "### Non-prod artifacts (exempt from gate)" in text
    # Each exemption line must end with `(token: <name>)`
    exempt_lines = [
        line
        for line in text.splitlines()
        if line.startswith("- `") and "(token:" in line
    ]
    assert exempt_lines, "Exemption fixture must have at least one (token: ...) line"
    for line in exempt_lines:
        # The path must contain the declared token
        path_match = re.match(r"^- `([^`]+)`.*\(token: ([a-z_]+)\)", line)
        assert path_match, f"Malformed exemption line: {line}"
        path, token = path_match.group(1), path_match.group(2)
        builtin_tokens = {"seed", "fixtures", "test", "__tests__"}
        assert token in path or token in builtin_tokens, (
            f"Exemption token '{token}' must appear in path or be a built-in token"
        )


def test_diff_fixtures_have_expected_status_letters():
    added = _read("diffs/migration-added.txt").strip().splitlines()
    assert all(line.split("\t")[0] == "A" for line in added if line), (
        "migration-added.txt must contain only A-status entries"
    )
    env = _read("diffs/env-var-added.txt").strip().splitlines()
    assert any(line.startswith("M\t.env.example") for line in env), (
        "env-var-added.txt must include a modified .env.example"
    )
    modified = _read("diffs/migration-modified.txt").strip().splitlines()
    assert any(line.startswith("M\tsupabase/migrations/") for line in modified), (
        "migration-modified.txt must include a modified migration file"
    )


@pytest.mark.parametrize(
    "fixture,required",
    [
        ("expected-outputs/post-automation-m1.md", ["### M1 migrations", "[evidence pending]"]),
        ("expected-outputs/post-automation-m2.md", ["### M2 env vars", "[evidence pending]"]),
    ],
)
def test_expected_output_snippets_have_class_heading_and_placeholder(fixture, required):
    text = _read(fixture)
    for needle in required:
        assert needle in text, f"{fixture} missing expected substring: {needle!r}"
