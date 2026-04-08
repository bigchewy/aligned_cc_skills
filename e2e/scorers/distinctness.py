"""
Inter-persona distinctness scorer for persona-panel eval scenarios.

Runs as a post-processing step AFTER `promptfoo eval` completes.
Parses persona-panel output into per-persona sections, computes pairwise
cosine similarity using embeddings, and reports pass/fail.

Usage:
    python scorers/distinctness.py results.json [--threshold 0.92]
"""

from __future__ import annotations

import re


def parse_persona_sections(output: str) -> list[dict]:
    """Extract individual persona sections from structured LLM output.

    Supports two formats:
    - Markdown headers: ## Persona Name
    - Numbered bold: 1. **Persona Name**

    Returns list of {"name": str, "content": str} dicts.
    Returns empty list if no recognizable persona structure found.
    """
    sections: list[dict] = []

    # Try markdown headers first: ## The Persona Name or ## Persona Name
    header_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    headers = list(header_pattern.finditer(output))

    if len(headers) >= 2:
        for i, match in enumerate(headers):
            name = match.group(1).strip()
            start = match.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(output)
            content = output[start:end].strip()
            sections.append({"name": name, "content": content})
        return sections

    # Try numbered bold: 1. **Persona Name**
    numbered_pattern = re.compile(
        r"^\d+\.\s+\*\*(.+?)\*\*\s*$", re.MULTILINE
    )
    numbered_headers = list(numbered_pattern.finditer(output))

    if len(numbered_headers) >= 2:
        for i, match in enumerate(numbered_headers):
            name = match.group(1).strip()
            start = match.end()
            end = (
                numbered_headers[i + 1].start()
                if i + 1 < len(numbered_headers)
                else len(output)
            )
            content = output[start:end].strip()
            sections.append({"name": name, "content": content})
        return sections

    # Single header — still return it
    if len(headers) == 1:
        name = headers[0].group(1).strip()
        content = output[headers[0].end() :].strip()
        sections.append({"name": name, "content": content})
        return sections

    if len(numbered_headers) == 1:
        name = numbered_headers[0].group(1).strip()
        content = output[numbered_headers[0].end() :].strip()
        sections.append({"name": name, "content": content})
        return sections

    return []
