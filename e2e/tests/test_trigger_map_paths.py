"""Validate trigger-map.yaml: paths exist, scenarios resolve, cross-validate against surface."""

from pathlib import Path

import pytest
import yaml

E2E_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = E2E_DIR.parent
TRIGGER_MAP_FILE = E2E_DIR / "trigger-map.yaml"
SURFACE_FILE = E2E_DIR / "eval-surface.yaml"


def load_trigger_map():
    with open(TRIGGER_MAP_FILE) as f:
        return yaml.safe_load(f)


def load_surface_patterns():
    with open(SURFACE_FILE) as f:
        data = yaml.safe_load(f)
    return data["patterns"]


def expand_pattern(pattern: str) -> list[Path]:
    return list(REPO_ROOT.glob(pattern))


TRIGGER_DATA = load_trigger_map()
SURFACE_PATTERNS = load_surface_patterns()


def all_trigger_paths():
    """Extract all unique paths from trigger-map entries."""
    paths = []
    for entry in TRIGGER_DATA["triggers"]:
        for p in entry["paths"]:
            paths.append(p)
    return paths


def all_scenario_paths():
    """Extract all unique scenario paths from trigger-map entries."""
    scenarios = []
    for entry in TRIGGER_DATA["triggers"]:
        for s in entry["scenarios"]:
            scenarios.append(s)
    return scenarios


@pytest.mark.parametrize("trigger_path", all_trigger_paths())
def test_trigger_path_exists_on_disk(trigger_path):
    """Every path in trigger-map.yaml must exist in the repo."""
    full_path = REPO_ROOT / trigger_path
    assert full_path.exists(), f"Trigger path not found: {trigger_path}"


@pytest.mark.parametrize("scenario_path", all_scenario_paths())
def test_scenario_resolves_relative_to_e2e(scenario_path):
    """Every scenario path must resolve relative to e2e/ directory."""
    full_path = E2E_DIR / scenario_path
    assert full_path.exists(), f"Scenario not found: {scenario_path} (resolved to {full_path})"


@pytest.mark.parametrize("trigger_path", all_trigger_paths())
def test_trigger_path_matches_surface_pattern(trigger_path):
    """Every trigger-map path must match at least one eval-surface pattern.

    This is the cross-validation invariant from the design doc:
    trigger-map is a subset of eval-surface.
    """
    matched = False
    for pattern in SURFACE_PATTERNS:
        matches = expand_pattern(pattern)
        for m in matches:
            if m == REPO_ROOT / trigger_path:
                matched = True
                break
        if matched:
            break
    assert matched, (
        f"Trigger path '{trigger_path}' does not match any eval-surface pattern. "
        f"Add a matching pattern to eval-surface.yaml."
    )


def test_trigger_map_is_flat_structure():
    """trigger-map.yaml must be a flat structure: triggers array of objects with string arrays."""
    assert "triggers" in TRIGGER_DATA, "Missing 'triggers' key"
    assert isinstance(TRIGGER_DATA["triggers"], list), "'triggers' must be a list"
    for i, entry in enumerate(TRIGGER_DATA["triggers"]):
        assert "paths" in entry, f"Entry {i} missing 'paths'"
        assert "scenarios" in entry, f"Entry {i} missing 'scenarios'"
        assert isinstance(entry["paths"], list), f"Entry {i} 'paths' must be a list"
        assert isinstance(entry["scenarios"], list), f"Entry {i} 'scenarios' must be a list"
        for p in entry["paths"]:
            assert isinstance(p, str), f"Entry {i} path must be string, got: {type(p)}"
        for s in entry["scenarios"]:
            assert isinstance(s, str), f"Entry {i} scenario must be string, got: {type(s)}"
