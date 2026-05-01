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
