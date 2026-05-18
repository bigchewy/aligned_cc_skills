"""Coverage test: every framework expected to populate `input_asks` declares it.

The `reverse-engineered-brand` orchestrator's PHASE 3.2 reads `input_asks` from each
owning framework's frontmatter. If the field is missing or malformed, the Inputs
Needed surface in `review.html` will silently render empty for that folder.
"""
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent

# Frameworks that must declare `input_asks` per the per-tab catalog in
# docs/plans/2026-05-17-reverse-engineered-brand-input-asks-design.md.
REQUIRED_FRAMEWORKS = [
    "5-components-positioning",
    "strategic-narrative",
    "messaging-distillation",
    "brand-voice",
    "buyer-persona",
    "competitive-battle-card",
    "proof-points-audit",
]

VALID_TIERS = {"critical", "recommended", "optional"}


def _read_frontmatter(prompt_path: Path) -> dict:
    text = prompt_path.read_text()
    assert text.startswith("---\n"), f"{prompt_path}: missing frontmatter"
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]) or {}


@pytest.mark.parametrize("framework_id", REQUIRED_FRAMEWORKS)
def test_framework_declares_input_asks(framework_id):
    prompt = REPO_ROOT / "frameworks" / framework_id / "prompt.md"
    fm = _read_frontmatter(prompt)
    asks = fm.get("input_asks")
    assert isinstance(asks, list) and asks, (
        f"{framework_id}: input_asks must be a non-empty list"
    )
    for i, entry in enumerate(asks):
        assert isinstance(entry, dict), f"{framework_id} input_asks[{i}]: must be a mapping"
        assert entry.get("tier") in VALID_TIERS, (
            f"{framework_id} input_asks[{i}].tier: must be one of {VALID_TIERS}, "
            f"got {entry.get('tier')!r}"
        )
        ask = entry.get("ask")
        assert isinstance(ask, str) and ask.strip(), (
            f"{framework_id} input_asks[{i}].ask: must be a non-empty string"
        )


def test_audience_taxonomy_has_ideal_inputs_section():
    """`audience-taxonomy.md` is not a framework prompt, so it carries its
    `input_asks` under a `## Ideal inputs` heading instead of in frontmatter."""
    taxonomy = REPO_ROOT / "frameworks" / "reverse-engineered-brand" / "audience-taxonomy.md"
    text = taxonomy.read_text()
    assert "\n## Ideal inputs\n" in text, (
        "audience-taxonomy.md must contain a `## Ideal inputs` section"
    )
    # The section must include at least one input_asks YAML block.
    assert "input_asks:" in text, (
        "audience-taxonomy.md `## Ideal inputs` must include an `input_asks:` block"
    )
