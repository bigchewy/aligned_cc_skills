"""Structural assertions for the brainstorming three-modes implementation."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_research_mini_protocol_has_required_sections():
    text = read("skills/brainstorming/references/research-mini-protocol.md")
    assert "## Phases" in text, "missing ## Phases section"
    assert "## Output contract" in text, "missing ## Output contract section"
    assert "## Recursion forbidden" in text, "missing ## Recursion forbidden section"
