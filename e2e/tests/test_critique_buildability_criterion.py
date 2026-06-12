"""Pins criterion 12 (Build & type-safety constraints) in the plan-critique
checklist and its Verifier routing.

Four incidents since 2026-05-16 in the Planted repo were defects that pass
Jest but fail `next build` — and one (2026-06-11 exercise-test-page) was
prescribed BY THE PLAN ITSELF and survived both critique rounds:
non-whitelisted named exports from page.tsx, 'use client' files importing
fs-using engine modules (hidden by jest.mock), and mocked-function
signature drift (only tsc-at-build compares call site to declaration).
Criterion 12 makes these plan-time blocking findings.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHECKLIST = (
    REPO_ROOT / "skills" / "writing-plans" / "plan-critique-checklist.md"
)
PANEL_PROMPTS = (
    REPO_ROOT
    / "skills"
    / "writing-plans"
    / "references"
    / "critique-panel-prompts.md"
)
CHECKLIST_TEXT = CHECKLIST.read_text(encoding="utf-8")
PANEL_TEXT = PANEL_PROMPTS.read_text(encoding="utf-8")


def test_checklist_has_criterion_12():
    assert "### 12. Build & type-safety constraints" in CHECKLIST_TEXT


def test_criterion_12_covers_page_export_whitelist():
    assert "generateStaticParams" in CHECKLIST_TEXT, (
        "Criterion 12 must enumerate the Next.js page-export whitelist"
    )
    assert "page.tsx" in CHECKLIST_TEXT


def test_criterion_12_covers_client_server_boundary():
    assert "'use client'" in CHECKLIST_TEXT
    assert "registry-loader" in CHECKLIST_TEXT, (
        "Criterion 12 must name the fs-using engine modules that must not "
        "be imported from client files"
    )


def test_criterion_12_covers_mocked_signature_drift():
    assert "mocked" in CHECKLIST_TEXT and "signature" in CHECKLIST_TEXT, (
        "Criterion 12 must require same-task declaration updates when a "
        "call site of a mocked function changes arguments"
    )


def test_checklist_count_updated_to_12():
    assert "the 12 criteria below" in CHECKLIST_TEXT
    assert "the 11 criteria below" not in CHECKLIST_TEXT


def test_results_table_has_row_12():
    assert "| 12 | Build & type-safety constraints |" in CHECKLIST_TEXT


def test_verifier_routes_criterion_12():
    assert "criteria 1, 2, 4, 7, 8, 12" in PANEL_TEXT, (
        "The Verifier's Phase 3 criteria list must include criterion 12"
    )
    assert "Criterion 12" in PANEL_TEXT, (
        "The Verifier prompt must carry a criterion-12 verification "
        "procedure"
    )
