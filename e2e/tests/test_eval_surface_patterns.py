"""Validate eval-surface.yaml: every pattern matches at least one file on disk."""

from pathlib import Path

import pytest
import yaml

E2E_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = E2E_DIR.parent
SURFACE_FILE = E2E_DIR / "eval-surface.yaml"


def load_surface_patterns():
    """Load patterns from eval-surface.yaml."""
    with open(SURFACE_FILE) as f:
        data = yaml.safe_load(f)
    return data["patterns"]


def expand_pattern(pattern: str) -> list[Path]:
    """Expand a glob pattern relative to repo root.

    Handles both directory globs (advisors/prompts/**)
    and specific-file patterns (skills/persona-panel/SKILL.md).
    """
    return list(REPO_ROOT.glob(pattern))


PATTERNS = load_surface_patterns()


@pytest.mark.parametrize("pattern", PATTERNS)
def test_pattern_matches_at_least_one_file(pattern):
    """Each surface pattern must match at least one file on disk."""
    matches = [m for m in expand_pattern(pattern) if m.is_file()]
    assert len(matches) > 0, f"Orphan pattern — no files match: {pattern}"


def test_surface_file_is_flat_list():
    """eval-surface.yaml must be a flat list of strings under 'patterns' key."""
    with open(SURFACE_FILE) as f:
        data = yaml.safe_load(f)
    assert "patterns" in data, "Missing 'patterns' key"
    assert isinstance(data["patterns"], list), "'patterns' must be a list"
    for item in data["patterns"]:
        assert isinstance(item, str), f"Pattern must be a string, got: {type(item)}"
