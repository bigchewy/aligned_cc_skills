"""Guard: every framework's advisor reference resolves against the in-scope advisor set.
This is the portability guarantee for the local-advisors migration — frameworks must move
WITH their advisors, or this goes red."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def _advisor_ids():
    with open(REPO / "advisors" / "registry.yaml") as f:
        data = yaml.safe_load(f)
    return {a["id"] for a in data["advisors"]}


def _frameworks():
    with open(REPO / "frameworks" / "registry.yaml") as f:
        data = yaml.safe_load(f)
    return data["frameworks"]


def test_every_framework_advisor_resolves():
    advisor_ids = _advisor_ids()
    dangling = [
        (e["id"], e["advisor"])
        for e in _frameworks()
        if e["advisor"] not in advisor_ids
    ]
    assert not dangling, (
        f"{len(dangling)} framework(s) reference an advisor not in advisors/registry.yaml — "
        f"the advisor must move WITH its frameworks: {dangling[:10]}"
    )


def test_no_framework_prompt_names_a_missing_advisor():
    """Scan each framework prompt.md first line ('You are {Advisor}, ...') and confirm the
    framework's registry advisor still resolves. Catches a prompt left behind after its
    advisor migrated."""
    advisor_ids = _advisor_ids()
    fw_dir = REPO / "frameworks"
    orphaned = []
    for e in _frameworks():
        prompt = fw_dir / e["id"] / "prompt.md"
        if not prompt.exists():
            continue
        if e["advisor"] not in advisor_ids:
            orphaned.append(e["id"])
    assert not orphaned, f"framework prompt(s) whose advisor no longer resolves: {orphaned[:10]}"
