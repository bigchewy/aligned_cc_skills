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
from pathlib import Path

DEFAULT_THRESHOLD = 0.92


def _slice_sections(output: str, matches: list) -> list[dict]:
    """Slice text between consecutive regex match positions into name/content dicts."""
    result = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(output)
        result.append({"name": m.group(1).strip(), "content": output[start:end].strip()})
    return result


def parse_persona_sections(output: str) -> list[dict]:
    """Extract individual persona sections from structured LLM output.

    Supports two formats:
    - Markdown headers: ## Persona Name
    - Numbered bold: 1. **Persona Name**

    Returns list of {"name": str, "content": str} dicts.
    Returns empty list if no recognizable persona structure found.

    Priority: a pattern with ≥2 matches wins over a single-match fallback —
    so a stray ## header in numbered output doesn't preempt the real format.
    """
    headers = list(re.finditer(r"^##\s+(.+)$", output, re.MULTILINE))
    numbered = list(re.finditer(r"^\d+\.\s+\*\*(.+?)\*\*\s*$", output, re.MULTILINE))

    if len(headers) >= 2:
        return _slice_sections(output, headers)
    if len(numbered) >= 2:
        return _slice_sections(output, numbered)
    if headers:
        return _slice_sections(output, headers)
    if numbered:
        return _slice_sections(output, numbered)
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

    Note: Only processes the first matching full-stack output. Multiple
    test cases in a single scenario will only score the first result.
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
        if idx + 1 >= len(sys.argv):
            print("Error: --threshold requires a numeric value")
            sys.exit(1)
        threshold = float(sys.argv[idx + 1])

    if not Path(results_path).exists():
        print(f"Error: results file not found: {results_path}")
        sys.exit(1)

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
