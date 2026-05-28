#!/usr/bin/env python3
"""Curate an aggregated open-questions queue into the thin Marley persisted shape.

Deterministic: the same input queue always yields the same curated set and the
same OQ-NNN ids. Invoked inline by the reverse-engineered-brand orchestrator at
PHASE 3 (no sub-agent, no LLM). Reads .build/slices/*.oq.json when run as a CLI;
the pure functions below are unit-tested directly.
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

FLOOR = 5   # backfill target: surface at least this many when owner-decisions are few
CAP = 15    # hard maximum curated questions

IMPACT_RANK = {"P0": 0, "P1": 1, "P2": 2}          # lower = higher priority
CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}  # low first (most uncertain)

# Conservative owner-authority classifier (R2): ratify / approve / name a category /
# confirm currency. Errs toward classifying as owner-authority when phrasing is ambiguous.
_OWNER_RE = re.compile(
    r"\b(ratif\w+|approv\w+|sign[\s-]?off|"
    r"confirm\w*|designat\w+|authoriz\w+|"
    r"default\s+category|name\s+the\s+category|"
    r"(still\s+)?current\b|currency\b|up[\s-]?to[\s-]?date|still\s+accurate)\b",
    re.IGNORECASE,
)


def is_owner_authority(oq: dict) -> bool:
    text = f"{oq.get('question') or ''} {oq.get('why_it_matters') or ''}"
    return bool(_OWNER_RE.search(text))


def _sort_key(item):
    agg_index, oq = item
    return (
        0 if is_owner_authority(oq) else 1,            # owner-authority first
        IMPACT_RANK.get(oq.get("impact"), 3),          # P0 > P1 > P2
        CONFIDENCE_RANK.get(oq.get("confidence"), 3),  # low-confidence first
        str(oq.get("file") or oq.get("slice") or ""),  # source slice id ASC
        agg_index,                                     # aggregation order ASC
    )


def curate(queue: list[dict]) -> list[dict]:
    """Return the curated subset of rich-shape OQs in display order."""
    if not queue:
        return []
    indexed = list(enumerate(queue))                    # preserve aggregation order
    ordered = sorted(indexed, key=_sort_key)
    owner = [item for item in ordered if is_owner_authority(item[1])]
    rest = [item for item in ordered if not is_owner_authority(item[1])]
    selected = list(owner)
    if len(selected) < FLOOR:
        selected.extend(rest[: FLOOR - len(selected)])
    selected = selected[:CAP]
    selected = sorted(selected, key=_sort_key)          # stable final display order
    return [item[1] for item in selected]


def curate_to_thin(queue: list[dict]) -> list[dict]:
    """Curate, then reshape to the 5-field persisted shape with OQ-NNN ids."""
    thin = []
    for i, oq in enumerate(curate(queue), start=1):
        thin.append({
            "id": f"OQ-{i:03d}",
            "slice": oq.get("file") or oq.get("slice") or "",
            "impact": oq.get("impact"),
            "question": (oq["question"] if "question" in oq else oq.get("inferred_value") or ""),
            "why_it_matters": oq.get("why_it_matters") or "",
        })
    return thin


def modal_confidence(levels: list) -> str:
    """Return modal confidence level; even 2-way tie between adjacent levels → compound string."""
    if not levels:
        return "medium"
    order = ["low", "medium", "high"]
    counts = {l: levels.count(l) for l in order}
    max_count = max(counts.values())
    winners = [l for l in order if counts[l] == max_count]
    if len(winners) == 1:
        return winners[0]
    # Even split between two adjacent levels → compound (e.g., "medium-high")
    if len(winners) == 2 and order.index(winners[1]) - order.index(winners[0]) == 1:
        return f"{winners[0]}-{winners[1]}"
    return winners[0]  # fallback: lowest of tied levels


def aggregate_build_dir(slices_dir: Path) -> list[dict]:
    """Concatenate open_questions from every *.oq.json, in alphabetical slice order."""
    queue = []
    for path in sorted(glob.glob(str(slices_dir / "**" / "*.oq.json"), recursive=True)):
        queue.extend(json.loads(Path(path).read_text()).get("open_questions", []))
    return queue


def main(argv) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: curate_open_questions.py <.build/slices dir>\n")
        return 2
    queue = aggregate_build_dir(Path(argv[1]))
    json.dump(curate_to_thin(queue), sys.stdout, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
