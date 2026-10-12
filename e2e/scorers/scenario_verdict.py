"""Turn one promptfoo JSON output file into a PASS, FAIL, or ERROR verdict.

Paired scenarios compare the full-stack answer (Aligned prompt) with the vanilla
and aware-but-unaided answers. Routing scenarios label every test "single" and
have no baseline. Scores are on the 1 to 5 scale set by providers/rubric-prompt.txt.
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

ARMS = {"full-stack", "vanilla", "aware", "single"}
FULL_STACK_MIN = 3.5
VANILLA_GAP_MIN = 1.0
AWARE_GAP_MIN = 0.5
SINGLE_MIN = 3.5
ERROR_FAILURE_REASON = 2
RATE_LIMIT_MARKERS = ("rate limit", "rate_limit", "usage limit")
RATE_LIMIT_CODE = re.compile(r"\b429\b")


def is_rate_limited(text):
    lowered = text.lower()
    return any(m in lowered for m in RATE_LIMIT_MARKERS) or bool(RATE_LIMIT_CODE.search(text))


@dataclass
class Verdict:
    verdict: str
    reason: str
    full_stack: float | None = None
    gap_vanilla: float | None = None
    gap_aware: float | None = None
    model: str = "unknown"
    rate_limited: bool = False


def _description(result):
    return (result.get("testCase") or {}).get("description") or result.get("description") or "unnamed test"


def _errors(results):
    """Return (display, raw) pairs. Only the raw text is checked for rate limits."""
    errors = []
    for r in results:
        if r.get("error") or r.get("failureReason") == ERROR_FAILURE_REASON:
            raw = str(r.get("error") or "")
            errors.append((f"{_description(r)}: {raw or 'provider error'}", raw))
        for c in (r.get("gradingResult") or {}).get("componentResults") or []:
            if (c.get("metadata") or {}).get("graderError"):
                raw = str(c.get("reason") or "")
                errors.append((f"{_description(r)}: judge failed: {raw}", raw))
    return errors


def _model(results):
    for r in results:
        usage = ((r.get("response") or {}).get("metadata") or {}).get("modelUsage") or {}
        if usage:
            return next(iter(usage))
    return "unknown"


def score_results(results):
    if not results:
        return Verdict("ERROR", "promptfoo output has no test results")
    errors = _errors(results)
    if errors:
        rate_limited = any(is_rate_limited(raw) for _, raw in errors)
        return Verdict("ERROR", "; ".join(display for display, _ in errors[:3]), rate_limited=rate_limited)

    by_arm = {}
    for r in results:
        arm = ((r.get("testCase") or {}).get("metadata") or {}).get("arm")
        if arm not in ARMS:
            return Verdict("ERROR", f"{_description(r)}: missing or unknown kind label {arm!r}")
        nested = (r.get("gradingResult") or {}).get("score")
        score = nested if nested is not None else r.get("score")
        try:
            value = float(score)
        except (TypeError, ValueError):
            return Verdict("ERROR", f"{_description(r)}: no numeric score")
        by_arm.setdefault(arm, []).append(value)
    model = _model(results)

    if "single" in by_arm:
        if set(by_arm) != {"single"}:
            return Verdict("ERROR", "scenario mixes single tests with paired tests", model=model)
        scores = by_arm["single"]
        low = [s for s in scores if s < SINGLE_MIN]
        avg = round(mean(scores), 2)
        if low:
            reason = f"{len(low)} of {len(scores)} tests below {SINGLE_MIN} (lowest {min(low):.2f})"
            return Verdict("FAIL", reason, full_stack=avg, model=model)
        return Verdict("PASS", "", full_stack=avg, model=model)

    if "full-stack" not in by_arm or "vanilla" not in by_arm:
        return Verdict("ERROR", "paired scenario needs a full-stack test and a vanilla test", model=model)
    full_stack = round(mean(by_arm["full-stack"]), 2)
    gap_vanilla = round(full_stack - mean(by_arm["vanilla"]), 2)
    gap_aware = round(full_stack - mean(by_arm["aware"]), 2) if "aware" in by_arm else None

    failures = []
    if full_stack < FULL_STACK_MIN:
        failures.append(f"full-stack {full_stack:.2f} below {FULL_STACK_MIN}")
    if gap_vanilla < VANILLA_GAP_MIN:
        failures.append(f"vanilla gap {gap_vanilla:.2f} below {VANILLA_GAP_MIN}")
    if gap_aware is not None and gap_aware < AWARE_GAP_MIN:
        failures.append(f"aware gap {gap_aware:.2f} below {AWARE_GAP_MIN}")
    return Verdict(
        "FAIL" if failures else "PASS",
        "; ".join(failures),
        full_stack=full_stack,
        gap_vanilla=gap_vanilla,
        gap_aware=gap_aware,
        model=model,
    )


def score_file(path):
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        return Verdict("ERROR", f"cannot read promptfoo output: {exc}")
    try:
        results = data["results"]["results"]
    except (KeyError, TypeError):
        return Verdict("ERROR", "promptfoo output has no results list")
    if not isinstance(results, list):
        return Verdict("ERROR", "promptfoo output has no results list")
    if not all(isinstance(r, dict) for r in results):
        return Verdict("ERROR", "promptfoo output has a result that is not an object")
    return score_results(results)
