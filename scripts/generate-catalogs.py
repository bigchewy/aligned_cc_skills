#!/usr/bin/env python3
"""Generate interactive HTML catalogs for frameworks and advisors.

Reads frameworks/registry.yaml and advisors/registry.yaml (and, for frameworks,
skills/playbook/layers.yaml to group them by layer and area), embeds the data
into a shared template at scripts/catalog-template.html, and writes the
output to docs/framework-catalog.html and docs/advisor-catalog.html.

Run: python3 scripts/generate-catalogs.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "scripts" / "catalog-template.html"
LAYERS_PATH = REPO_ROOT / "skills" / "playbook" / "layers.yaml"
OUTPUTS = [
    {
        "title": "Framework Catalog",
        "entity_type": "framework",
        "registry_path": REPO_ROOT / "frameworks" / "registry.yaml",
        "output_path": REPO_ROOT / "docs" / "framework-catalog.html",
    },
    {
        "title": "Advisor Catalog",
        "entity_type": "advisor",
        "registry_path": REPO_ROOT / "advisors" / "registry.yaml",
        "output_path": REPO_ROOT / "docs" / "advisor-catalog.html",
    },
]


def load_playbook() -> dict:
    """Layers, areas and the holding list from skills/playbook/layers.yaml, for grouping frameworks."""
    with LAYERS_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return {
        "layers": [
            {
                "id": layer["id"],
                "name": layer["name"],
                "areas": [
                    {"id": a["id"], "name": a["name"], "frameworks": list(a["frameworks"])}
                    for a in layer["areas"]
                ],
            }
            for layer in data["layers"]
        ],
        "holding": data.get("holding", []),
    }


def build_config(entity_type: str, registry: dict, generated_at: str) -> dict:
    config = {
        "entityType": entity_type,
        "registry": registry,
        "generatedAt": generated_at,
    }
    if entity_type == "framework":
        config["playbook"] = load_playbook()
    return config


def main() -> int:
    if not TEMPLATE_PATH.exists():
        print(f"ERROR: template not found at {TEMPLATE_PATH}", file=sys.stderr)
        return 1

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    generated_at = datetime.now(timezone.utc).isoformat()

    for spec in OUTPUTS:
        if not spec["registry_path"].exists():
            print(f"ERROR: registry not found at {spec['registry_path']}", file=sys.stderr)
            return 1

        with spec["registry_path"].open("r", encoding="utf-8") as fh:
            registry = yaml.safe_load(fh)

        config = build_config(spec["entity_type"], registry, generated_at)
        config_json = json.dumps(config, ensure_ascii=False)
        # Defensive: escape any "</script>" sequences inside JSON so the
        # embedded <script type="application/json"> block stays well-formed.
        config_json = config_json.replace("</script>", "<\\/script>")

        rendered = template.replace("__TITLE__", spec["title"])
        rendered = rendered.replace("__CONFIG_JSON__", config_json)

        spec["output_path"].write_text(rendered, encoding="utf-8")

        count = len((registry or {}).get(
            "frameworks" if spec["entity_type"] == "framework" else "advisors",
            []
        ))
        print(f"Wrote {spec['output_path'].relative_to(REPO_ROOT)} ({count} entries)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
