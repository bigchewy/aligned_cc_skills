"""Run promptfoo eval scenarios through the Claude Code login.

From e2e/:
  npm run eval                          scenarios mapped from changed files
  npm run eval -- <scenario.yaml> ...   named scenarios
  npm run eval -- --all                 every scenario (ask the user first)
  npm run eval -- --resume <run id>     finish a stopped run

Exit codes: 0 all passed or nothing to run, 1 a scenario failed or errored,
2 usage error or the run stopped on a rate limit.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from scorers.scenario_verdict import Verdict, is_rate_limited, score_file

E2E = Path(__file__).resolve().parent
REPO = E2E.parent
RUNS_DIR = E2E / "output" / "runs"
PROMPTFOO = E2E / "node_modules" / ".bin" / "promptfoo"
SHARED_FILES = {"e2e/providers/claude-login.yaml", "e2e/providers/rubric-prompt.txt"}
OK_EXIT_CODES = {0, 100}


@dataclass
class Selection:
    scenarios: list
    shared_changed: list
    unmapped: list


def all_scenarios():
    return sorted(str(p.relative_to(E2E)) for p in (E2E / "scenarios").rglob("*.yaml"))


def load_triggers():
    return yaml.safe_load((E2E / "trigger-map.yaml").read_text())["triggers"]


def load_patterns():
    return yaml.safe_load((E2E / "eval-surface.yaml").read_text())["patterns"]


def changed_files(base, run=subprocess.run):
    commands = [
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    files = set()
    for cmd in commands:
        proc = run(cmd, cwd=REPO, capture_output=True, text=True, check=True)
        files.update(line.strip() for line in proc.stdout.splitlines() if line.strip())
    return sorted(files)


def matches_surface(path, pattern):
    """Glob match where `**/` is zero or more directories, `*` and `?` stay in one segment."""
    regex, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            regex += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            regex += ".*"
            i += 2
        elif pattern[i] == "*":
            regex += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            regex += "[^/]"
            i += 1
        else:
            regex += re.escape(pattern[i])
            i += 1
    return re.fullmatch(regex, path) is not None


def select_scenarios(changed, triggers, patterns):
    picked, shared, unmapped = set(), [], []
    for path in changed:
        if path in SHARED_FILES:
            shared.append(path)
            continue
        if path.startswith("e2e/scenarios/") and path.endswith(".yaml"):
            picked.add(path[len("e2e/"):])
            continue
        hits = [t for t in triggers if path in t["paths"]]
        for trigger in hits:
            picked.update(trigger["scenarios"])
        if not hits and any(matches_surface(path, p) for p in patterns):
            unmapped.append(path)
    scenarios = sorted(s for s in picked if (E2E / s).is_file())
    return Selection(scenarios=scenarios, shared_changed=shared, unmapped=unmapped)


def estimate_calls(scenarios):
    total = 0
    for scenario in scenarios:
        data = yaml.safe_load((E2E / scenario).read_text())
        rubrics = len((data.get("defaultTest") or {}).get("assert") or [])
        total += len(data.get("tests") or []) * (1 + rubrics)
    return total


def child_env(use_api_key, base_env):
    env = dict(base_env)
    env.pop("CLAUDE_PID", None)
    if not use_api_key:
        env.pop("ANTHROPIC_API_KEY", None)
    env["PROMPTFOO_ASSERTIONS_MAX_CONCURRENCY"] = "2"
    return env


def output_name(scenario):
    return scenario.removeprefix("scenarios/").removesuffix(".yaml").replace("/", "__") + ".json"


def promptfoo_command(scenario, out_path):
    return [
        str(PROMPTFOO), "eval", "-c", scenario, "-o", str(out_path),
        "--max-concurrency", "2", "--no-cache", "--no-write", "--no-progress-bar",
    ]


def run_scenario(scenario, run_dir, env, run=subprocess.run):
    out = run_dir / output_name(scenario)
    try:
        proc = run(promptfoo_command(scenario, out), cwd=E2E, env=env, capture_output=True, text=True)
    except OSError as exc:
        return Verdict("ERROR", f"promptfoo did not start: {exc}")
    if proc.returncode not in OK_EXIT_CODES:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:] or ["no output"]
        rate_limited = is_rate_limited(proc.stderr or "")
        return Verdict("ERROR", f"promptfoo exited {proc.returncode}: {tail[0]}", rate_limited=rate_limited)
    return score_file(out)


def _fmt(value):
    return "" if value is None else f"{value:.2f}"


def write_summary(run_dir, rows):
    models = sorted({v.model for _, v in rows if v.model != "unknown"}) or ["unknown"]
    lines = [
        f"# Eval run {run_dir.name}",
        "",
        f"Model: {', '.join(models)}",
        "",
        "| Scenario | Verdict | Full-stack | Gap vs vanilla | Gap vs aware | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for scenario, v in rows:
        lines.append(
            f"| {scenario} | {v.verdict} | {_fmt(v.full_stack)} | {_fmt(v.gap_vanilla)} "
            f"| {_fmt(v.gap_aware)} | {v.reason} |"
        )
    text = "\n".join(lines) + "\n"
    (run_dir / "summary.md").write_text(text)
    return text


def _normalize(path):
    path = path.removeprefix("e2e/")
    return path if (E2E / path).is_file() and path.startswith("scenarios/") else None


def _parse(argv):
    parser = argparse.ArgumentParser(prog="npm run eval --", description=__doc__.splitlines()[0])
    parser.add_argument("scenarios", nargs="*", help="scenario files to run")
    parser.add_argument("--all", action="store_true", help="run every scenario")
    parser.add_argument("--resume", metavar="RUN_ID", help="finish a stopped run")
    parser.add_argument("--base", default="main", help="branch to compare against (default main)")
    parser.add_argument("--use-api-key", action="store_true", help="keep ANTHROPIC_API_KEY for contributors with no Claude Code login")
    return parser.parse_args(argv)


def main(argv, run=subprocess.run):
    args = _parse(argv)
    if sum([bool(args.scenarios), args.all, bool(args.resume)]) > 1:
        print("Pick one: scenario paths, --all, or --resume.")
        return 2

    if args.resume:
        run_dir = RUNS_DIR / args.resume
        if not (run_dir / "scenarios.json").is_file():
            print(f"No run named {args.resume} in {RUNS_DIR}.")
            return 2
        scenarios = json.loads((run_dir / "scenarios.json").read_text())
    else:
        if args.all:
            scenarios = all_scenarios()
        elif args.scenarios:
            scenarios = [_normalize(p) for p in args.scenarios]
            if None in scenarios:
                bad = [p for p, s in zip(args.scenarios, scenarios) if s is None]
                print(f"Not a scenario file: {', '.join(bad)}")
                return 2
        else:
            try:
                changed = changed_files(args.base, run=run)
            except subprocess.CalledProcessError as exc:
                print(f"git failed: {(exc.stderr or '').strip()}")
                return 2
            sel = select_scenarios(changed, load_triggers(), load_patterns())
            for path in sel.shared_changed:
                print(f"{path} changed. It affects every scenario. Run `npm run eval -- --all` if you want all of them.")
            if sel.unmapped:
                print(f"{len(sel.unmapped)} changed prompt files have no scenario in trigger-map.yaml: {', '.join(sel.unmapped)}")
            scenarios = sel.scenarios
            if not scenarios:
                print("No changed files map to an eval scenario. Nothing to run.")
                return 0
        run_dir = RUNS_DIR / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "scenarios.json").write_text(json.dumps(scenarios, indent=2))

    print(f"Run {run_dir.name}: {len(scenarios)} scenarios, about {estimate_calls(scenarios)} Claude calls.")
    env = child_env(args.use_api_key, os.environ)
    rows = []
    for scenario in scenarios:
        out = run_dir / output_name(scenario)
        if out.is_file():
            verdict = score_file(out)
        else:
            print(f"Running {scenario}")
            verdict = run_scenario(scenario, run_dir, env, run=run)
        if verdict.rate_limited:
            out.unlink(missing_ok=True)
            print(f"Stopped on a rate limit at {scenario}: {verdict.reason}")
            print(f"Resume later with: npm run eval -- --resume {run_dir.name}")
            write_summary(run_dir, rows)
            return 2
        rows.append((scenario, verdict))

    print(write_summary(run_dir, rows))
    return 0 if all(v.verdict == "PASS" for _, v in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
