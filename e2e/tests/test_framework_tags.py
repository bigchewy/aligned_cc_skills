"""Stage and market tags on the framework registry."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FRAMEWORKS = ROOT / "frameworks" / "registry.yaml"
STAGES = ["idea", "pilot", "nail-it", "scale-it", "milk-it"]
MARKETS = ("b2b", "b2c")


def registry():
    with open(FRAMEWORKS, encoding="utf-8") as fh:
        return {f["id"]: f for f in yaml.safe_load(fh)["frameworks"]}


def test_stages_are_allowed_unique_and_in_lifecycle_order():
    for fid, entry in registry().items():
        if "stages" not in entry:
            continue
        stages = entry["stages"]
        assert stages, f"{fid}: stages is empty, leave it off instead"
        assert all(s in STAGES for s in stages), f"{fid}: unknown stage in {stages}"
        assert len(set(stages)) == len(stages), f"{fid}: duplicate stage"
        assert stages == sorted(stages, key=STAGES.index), f"{fid}: stages out of order"


def test_market_is_b2b_or_b2c():
    for fid, entry in registry().items():
        if "market" in entry:
            assert entry["market"] in MARKETS, f"{fid}: market {entry['market']!r}"


def test_spot_values_from_the_spec():
    reg = registry()
    assert reg["chj-operating-review"]["stages"] == ["scale-it", "milk-it"]
    assert reg["mochary-weekly-check-in"]["stages"] == ["pilot", "nail-it", "scale-it", "milk-it"]
    for fid in ("psiu-role-fit", "kernel-of-good-strategy"):
        assert "stages" not in reg[fid]
    for fid in ("origin-story-interview", "smallest-viable-audience"):
        assert "market" not in reg[fid]
