"""
Inter-persona distinctness scorer for persona-panel eval scenarios.

Runs as a post-processing step AFTER `promptfoo eval` completes.
Parses persona-panel output into per-persona sections, computes pairwise
cosine similarity using embeddings, and reports pass/fail.

Usage:
    python scorers/distinctness.py results.json [--threshold 0.92]
"""

from __future__ import annotations

import json
import re
import sys
from itertools import combinations

DEFAULT_THRESHOLD = 0.92


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


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings from OpenAI text-embedding-3-small.

    Uses OpenAI because distinctness measurement doesn't need large
    embeddings — small model is cheaper and sufficient for cosine distance.
    """
    from openai import OpenAI

    client = OpenAI()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def compute_pairwise_similarity(
    sections: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    """Compute pairwise cosine similarity across persona sections.

    Returns:
        {
            "pass": bool,
            "max_similarity": float,
            "pairs": [{"a": str, "b": str, "similarity": float}, ...],
            "skipped": False,
        }
        On API error:
        {"skipped": True, "reason": str}
    """
    texts = [s["content"] for s in sections]

    try:
        embeddings = get_embeddings(texts)
    except Exception as e:
        return {
            "skipped": True,
            "reason": f"Embedding API error: {e}",
        }

    pairs = []
    max_sim = 0.0
    for i, j in combinations(range(len(sections)), 2):
        sim = _cosine_similarity(embeddings[i], embeddings[j])
        pairs.append({
            "a": sections[i]["name"],
            "b": sections[j]["name"],
            "similarity": round(sim, 4),
        })
        max_sim = max(max_sim, sim)

    return {
        "pass": max_sim < threshold,
        "max_similarity": round(max_sim, 4),
        "pairs": pairs,
        "threshold": threshold,
        "skipped": False,
    }


def score_results(
    results_data: dict,
    scenario_filter: str = "persona-panel",
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    """Score distinctness from Promptfoo results JSON.

    Filters for full-stack provider results from persona-panel scenarios,
    parses persona sections, and computes similarity.
    """
    results_list = results_data.get("results", {}).get("results", [])

    full_stack_outputs = []
    for r in results_list:
        provider_label = r.get("provider", {}).get("label", "")
        description = r.get("description", "")
        if provider_label == "full-stack" and scenario_filter in description.lower():
            output = r.get("response", {}).get("output", "")
            if output:
                full_stack_outputs.append(output)

    if not full_stack_outputs:
        return {"skipped": True, "reason": "No full-stack outputs found in results"}

    sections = parse_persona_sections(full_stack_outputs[0])

    if len(sections) < 2:
        return {"skipped": True, "reason": "Unparseable: fewer than 2 persona sections found"}

    return compute_pairwise_similarity(sections, threshold=threshold)


def main():
    """CLI entry point: python scorers/distinctness.py results.json [--threshold 0.92]"""
    if len(sys.argv) < 2:
        print("Usage: python scorers/distinctness.py <results.json> [--threshold 0.92]")
        sys.exit(1)

    results_path = sys.argv[1]
    threshold = DEFAULT_THRESHOLD

    if "--threshold" in sys.argv:
        idx = sys.argv.index("--threshold")
        threshold = float(sys.argv[idx + 1])

    with open(results_path) as f:
        results_data = json.load(f)

    result = score_results(results_data, threshold=threshold)

    print(json.dumps(result, indent=2))

    if result.get("skipped"):
        print(f"\nWARNING: Distinctness check skipped — {result['reason']}")
        sys.exit(0)

    if result["pass"]:
        print(f"\nPASS: Max similarity {result['max_similarity']} < {threshold}")
    else:
        print(f"\nFAIL: Max similarity {result['max_similarity']} >= {threshold}")
        sys.exit(1)


if __name__ == "__main__":
    main()
