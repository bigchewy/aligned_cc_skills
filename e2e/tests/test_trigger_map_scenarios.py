"""Validate trigger-map scenarios are registered in promptfooconfig.yaml."""

from pathlib import Path

import yaml

E2E_DIR = Path(__file__).resolve().parent.parent
TRIGGER_MAP_FILE = E2E_DIR / "trigger-map.yaml"
PROMPTFOO_CONFIG = E2E_DIR / "promptfooconfig.yaml"


def test_all_trigger_scenarios_in_promptfoo_config():
    """Every scenario in trigger-map.yaml must appear in promptfooconfig.yaml imports."""
    with open(TRIGGER_MAP_FILE) as f:
        trigger_data = yaml.safe_load(f)

    with open(PROMPTFOO_CONFIG) as f:
        promptfoo_data = yaml.safe_load(f)

    # Extract scenario imports from promptfooconfig.yaml
    # Format: "file://scenarios/persona-panel/pricing-page.yaml"
    registered = set()
    for entry in promptfoo_data.get("scenarios", []):
        if isinstance(entry, str) and entry.startswith("file://"):
            registered.add(entry[len("file://"):])
        elif isinstance(entry, dict) and "file" in entry:
            registered.add(entry["file"])

    # Extract all unique scenarios from trigger-map
    trigger_scenarios = set()
    for entry in trigger_data["triggers"]:
        for s in entry["scenarios"]:
            trigger_scenarios.add(s)

    missing = trigger_scenarios - registered
    assert not missing, (
        f"Trigger-map scenarios not registered in promptfooconfig.yaml: {missing}. "
        f"Add 'file://<path>' entries to promptfooconfig.yaml's scenarios list."
    )
