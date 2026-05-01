"""Static-parse tests for the plan-manifest schema doc and writing-plans
authoring/critique additions."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SHARED_DIR = REPO_ROOT / "skills" / "_shared"
WRITING_PLANS = REPO_ROOT / "skills" / "writing-plans"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_manifest_format_doc_exists():
    p = SHARED_DIR / "plan-manifest-format.md"
    assert p.is_file(), "skills/_shared/plan-manifest-format.md must exist"
    text = _read(p)
    for field in ("mcp-tools-required", "env-vars-required"):
        assert field in text, f"manifest doc must specify field: {field}"
    # Must explain the .mcp.json resolution and the settings.local.json check
    assert ".mcp.json" in text
    assert "settings.local.json" in text or "permissions.allow" in text


def test_writing_plans_documents_manifest_authoring():
    skill = WRITING_PLANS / "SKILL.md"
    text = _read(skill)
    # Match the section heading specifically (`## Plan Manifest`), not a
    # casual mention earlier in the doc
    assert "## Plan Manifest" in text or "## Manifest Authoring" in text, \
        "writing-plans must document the manifest-authoring step"
    assert "plan-manifest-format.md" in text, \
        "writing-plans must reference _shared/plan-manifest-format.md"
    # Step must run BEFORE the manual-deploy scan AND before the critique
    # panel — so anchor on the heading positions, not a substring search
    manifest_idx = text.find("## Plan Manifest")
    if manifest_idx == -1:
        manifest_idx = text.find("## Manifest Authoring")
    deploy_idx = text.find("## Manual Deploy Artifact Scan")
    critique_idx = text.find("## Fact-Check + Critique Panel")
    assert manifest_idx >= 0
    assert deploy_idx > manifest_idx, \
        "Manifest-authoring section must precede ## Manual Deploy Artifact Scan"
    assert critique_idx > manifest_idx, \
        "Manifest-authoring section must precede ## Fact-Check + Critique Panel"
