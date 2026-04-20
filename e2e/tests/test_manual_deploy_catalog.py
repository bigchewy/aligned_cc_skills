"""Validate manual-deploy-artifact-catalog.md schema: every entry has required
prose sections, a single fenced yaml block with allowed fields, and severity
matching the parent section."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

E2E_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = E2E_DIR.parent
CATALOG_FILE = REPO_ROOT / "skills" / "_shared" / "manual-deploy-artifact-catalog.md"

ALLOWED_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
REQUIRED_PROSE_HEADERS = (
    "**Why it needs manual deploy:**",
    "**Detection:**",
    "**Prod step (for the plan entry):**",
    "**Plan section populated:**",
)


def _read_catalog() -> str:
    return CATALOG_FILE.read_text(encoding="utf-8")


def _section_severity(text: str, entry_start: int) -> str | None:
    """Find the nearest preceding `## <SEVERITY> —` section header."""
    header_re = re.compile(r"^## (CRITICAL|HIGH|MEDIUM|LOW) —", re.MULTILINE)
    last = None
    for m in header_re.finditer(text):
        if m.start() < entry_start:
            last = m.group(1)
        else:
            break
    return last


def _iter_entries(text: str):
    """Yield (entry_id, entry_body, parent_severity) tuples.

    An entry starts with `### <ID>: <Title>` and ends at the next `###` heading
    or a following `## ` (severity) heading, whichever comes first.
    """
    entry_starts = list(re.finditer(r"^### (M\d+): ", text, re.MULTILINE))
    next_h2 = list(re.finditer(r"^## ", text, re.MULTILINE))
    for i, m in enumerate(entry_starts):
        entry_id = m.group(1)
        body_start = m.end()
        next_h3 = entry_starts[i + 1].start() if i + 1 < len(entry_starts) else len(text)
        # Also stop at the next `## ` if it precedes the next `###`.
        stop_h2 = next((h2.start() for h2 in next_h2 if h2.start() > body_start), len(text))
        body_end = min(next_h3, stop_h2)
        parent = _section_severity(text, m.start())
        yield entry_id, text[body_start:body_end], parent


def test_catalog_file_exists():
    assert CATALOG_FILE.exists(), f"Catalog file missing: {CATALOG_FILE}"


def test_catalog_has_schema_header():
    text = _read_catalog()
    assert "## Schema" in text, "Catalog must contain a '## Schema' section"


def test_catalog_has_builtin_exemption_patterns():
    text = _read_catalog()
    assert "**/seed/**" in text
    assert "**/fixtures/**" in text
    assert "**/__tests__/**" in text
    assert "**/*.test.*" in text


def test_catalog_has_at_least_one_entry():
    text = _read_catalog()
    entries = list(_iter_entries(text))
    assert entries, "Catalog must contain at least one entry (### M<n>: ...)"


@pytest.mark.parametrize("entry_id,body,parent_severity", list(_iter_entries(_read_catalog())))
def test_entry_has_required_prose_headers(entry_id, body, parent_severity):
    for header in REQUIRED_PROSE_HEADERS:
        assert header in body, f"Entry {entry_id} missing prose header: {header}"


@pytest.mark.parametrize("entry_id,body,parent_severity", list(_iter_entries(_read_catalog())))
def test_entry_has_exactly_one_fenced_yaml_block(entry_id, body, parent_severity):
    blocks = re.findall(r"```yaml\n(.*?)```", body, re.DOTALL)
    assert len(blocks) == 1, (
        f"Entry {entry_id} must have exactly one ```yaml fenced block, found {len(blocks)}"
    )


@pytest.mark.parametrize("entry_id,body,parent_severity", list(_iter_entries(_read_catalog())))
def test_entry_yaml_block_has_allowed_fields(entry_id, body, parent_severity):
    blocks = re.findall(r"```yaml\n(.*?)```", body, re.DOTALL)
    data = yaml.safe_load(blocks[0])
    assert isinstance(data, dict), f"Entry {entry_id} yaml block must parse to a mapping"
    # Must have detector_glob or detector_grep (or both)
    assert "detector_glob" in data or "detector_grep" in data, (
        f"Entry {entry_id} must define detector_glob or detector_grep"
    )
    # severity
    assert "severity" in data, f"Entry {entry_id} missing severity"
    assert data["severity"] in ALLOWED_SEVERITIES, (
        f"Entry {entry_id} severity must be one of {ALLOWED_SEVERITIES}"
    )
    assert data["severity"] == parent_severity, (
        f"Entry {entry_id} severity {data['severity']!r} does not match parent "
        f"section {parent_severity!r}"
    )
    # evidence
    assert "evidence" in data and isinstance(data["evidence"], dict), (
        f"Entry {entry_id} missing 'evidence' map"
    )
    assert "kind" in data["evidence"] and data["evidence"]["kind"], (
        f"Entry {entry_id} evidence.kind must be non-empty"
    )
    assert "template" in data["evidence"] and data["evidence"]["template"], (
        f"Entry {entry_id} evidence.template must be non-empty"
    )
