"""Structural fixture-driven test for the manual-deploy Post-Automation
section shape. Validates the expected post-scan plan layout — the mechanical
contract the writing-plans scan step is expected to produce, and the shape
Step 0.5 relies on for parsing. Does not invoke the LLM; behavioral coverage
lives in the promptfoo eval scenarios under e2e/scenarios/manual-deploy/."""

from __future__ import annotations

from pathlib import Path

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


def test_diff_fixtures_have_expected_status_letters():
    added = _read("diffs/migration-added.txt").strip().splitlines()
    assert all(line.split("\t")[0] == "A" for line in added if line), (
        "migration-added.txt must contain only A-status entries"
    )
    modified = _read("diffs/migration-modified.txt").strip().splitlines()
    assert any(line.startswith("M\tsupabase/migrations/") for line in modified), (
        "migration-modified.txt must include a modified migration file"
    )


def test_expected_output_snippet_m1_has_class_heading():
    text = _read("expected-outputs/post-automation-m1.md")
    assert "### M1 migrations" in text
