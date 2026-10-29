"""find-potential-advisors runs every phase, and its report shows the evidence.

Eight runs between 2026-09-29 and 2026-10-28 folded research, candidate
profiles and evaluation into one wave of "research this area" agents. None
ran the separate evaluation agents. Ratings came from search snippets and
memory, voice samples were invented, and the cuts were only admitted when
the user asked. The fix moves the phases into a Workflow script that launches
every agent itself, computes the ratings in code from cited sources, and ends
with a fresh agent that checks the report.

The workflow tests run workflow.js under Node with stub agent() calls, so they
make no Claude calls.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "find-potential-advisors"
SKILL = SKILL_DIR / "SKILL.md"
WORKFLOW = SKILL_DIR / "workflow.js"
PROMPTS = SKILL_DIR / "agent-prompts.md"
TEMPLATE = SKILL_DIR / "report-template.md"
EXAMPLES = SKILL_DIR / "examples.md"
ANTI_EXAMPLES = SKILL_DIR / "anti-examples.md"


def _read(path):
    return path.read_text(encoding="utf-8")


def _section(text, heading):
    assert heading in text, f"missing section {heading}"
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


# --- SKILL.md -----------------------------------------------------------------


def test_description_says_when_to_use_it():
    front = _read(SKILL).split("---", 2)[1]
    description = re.search(r"^description:\s*\"?(.+?)\"?\s*$", front, re.M).group(1)
    assert description.startswith("Use when")


def test_skill_runs_the_workflow_script_when_the_tool_exists():
    text = _read(SKILL)
    assert "Workflow" in text
    assert "{base-directory}/workflow.js" in text
    assert "scriptPath" in text


def test_skill_has_an_agent_fallback_that_reads_the_same_prompts():
    fallback = _section(_read(SKILL), "## If the Workflow tool is not available")
    assert "Agent" in fallback
    assert "agent-prompts.md" in fallback
    # Evaluation must be done by a different agent from the one that profiled.
    assert "different agent" in fallback.lower()


def test_interview_skips_only_what_it_already_knows():
    # The user's rule (2026-10-28): skip a question when highly confident of the
    # answer, never on a significant guess, and say the assumption so it can be fixed.
    phase1 = _section(_read(SKILL), "## Phase 1").lower()
    assert "highly confident" in phase1
    assert "guess" in phase1
    assert "overlap" in phase1
    assert "assumption" in phase1
    assert "even when the user's message answers everything else" not in phase1


def test_skill_names_the_failures_it_guards_against():
    text = _read(SKILL).lower()
    assert "## red flags" in text
    for phrase in ["merge", "search snippet", "from memory", "skipped"]:
        assert phrase in text, phrase


def test_chat_summary_must_list_what_was_skipped():
    text = _read(SKILL)
    assert "What was skipped or not verified" in text


# --- supporting files ---------------------------------------------------------


def test_report_template_has_required_sections():
    text = _read(TEMPLATE)
    for heading in [
        "## Brief",
        "## Research",
        "## Candidates",
        "## Evaluation",
        "## Finalists",
        "## Recommendation",
        "## What was skipped or not verified",
        "## Run record",
        "## Chat summary",
    ]:
        assert heading in text, heading


def test_report_template_evaluation_shows_its_sources():
    evaluation = _section(_read(TEMPLATE), "## Evaluation")
    assert "URL" in evaluation
    assert "minutes" in evaluation.lower()
    assert "sum" in evaluation.lower()


def test_voice_sample_is_built_from_real_quotes():
    finalists = _section(_read(TEMPLATE), "## Finalists")
    assert "quote" in finalists.lower()
    assert "URL" in finalists


def test_examples_and_anti_examples_exist_with_real_cases():
    examples = _read(EXAMPLES)
    anti = _read(ANTI_EXAMPLES).lower()
    assert "http" in examples
    for phrase in ["one wave", "did not verify the hour count", "from memory", "only when asked"]:
        assert phrase in anti, phrase


def test_every_prompt_role_has_a_section():
    text = _read(PROMPTS)
    for heading in [
        "## Research",
        "## Candidates",
        "## Profile",
        "## Evaluate",
        "## Finalists",
        "## Write",
        "## Check",
        "## Fix",
    ]:
        assert heading in text, heading


# --- workflow.js under Node ---------------------------------------------------

HARNESS = r"""
const calls = [];
const scenario = JSON.parse(process.env.SCENARIO);
const people = scenario.people;

function namesIn(prompt) {
  return Object.keys(people).filter((n) => prompt.includes(n));
}

globalThis.args = scenario.args;
globalThis.log = () => {};
globalThis.phase = () => {};
globalThis.parallel = async (thunks) =>
  Promise.all(thunks.map((t) => t().catch(() => null)));
globalThis.pipeline = async (items, ...stages) =>
  Promise.all(items.map(async (item, i) => {
    let value = item;
    for (const stage of stages) {
      // Like the real pipeline(): a throw ends the chain, a null is passed on.
      try { value = await stage(value, item, i); } catch { return null; }
    }
    return value;
  }));

let checks = 0;
globalThis.agent = async (prompt, opts = {}) => {
  const label = opts.label || '';
  const role = label.split(':')[0];
  calls.push({ role, label, prompt });
  if (scenario.nullRoles.includes(role)) return null;
  switch (role) {
    case 'research':
      return { findings: [{ claim: 'x', source_url: 'https://a' }], names_mentioned: [], pages_opened: 3 };
    case 'candidates':
      return { candidates: Object.keys(people).map((name) => ({ name, why_considered: 'fit', source_url: 'https://c' })) };
    case 'profile':
      return { profiles: namesIn(prompt).map((name) => ({ name, credentials: 'c', approach: 'a', fit: 'f', sources: ['https://p'] })) };
    case 'evaluate':
      return { evaluations: namesIn(prompt).map((name) => ({ name, ...people[name] })) };
    case 'finalists':
      return { finalists: namesIn(prompt).slice(0, 2).map((name) => ({ name })), recommendation: 'A' };
    case 'write':
      return { brief_path: scenario.args.brief_path };
    case 'check':
      checks += 1;
      return { problems: checks === 1 ? scenario.firstCheckProblems : [] };
    case 'fix':
      return { fixed: true };
    default:
      return null;
  }
};

const mod = await import(process.env.WORKFLOW_COPY);
"""

# The script's return value is captured by wrapping its body; see _run.


def _person(books=0, minutes=0, terms=0, url=True):
    u = "https://x" if url else ""
    return {
        "books": [{"title": f"B{i}", "year": 2000, "url": u} for i in range(books)],
        "talks": [{"title": "T", "minutes": minutes, "url": u}] if minutes else [],
        "distinctive_terms": [{"term": f"t{i}", "url": u} for i in range(terms)],
        "quotes": [{"text": "q", "url": u}],
    }


PEOPLE = {
    "Ada High": _person(books=2, minutes=360, terms=3),
    "Ben Medium": _person(books=1, minutes=30, terms=1),
    "Cy Low": _person(books=0, minutes=60, terms=0),
    "Di Unsourced": _person(books=3, minutes=600, terms=4, url=False),
}

BASE_ARGS = {
    "brief_path": "/tmp/brief.md",
    "skill_dir": "/skill",
    "candidate_count": 4,
    "research_questions": ["Q one?", "Q two?", "Q three?"],
    "exclude": ["Existing Person"],
}


def _run(tmp_path, people=None, null_roles=(), first_check_problems=()):
    if shutil.which("node") is None:
        pytest.skip("node is not installed")
    body = _read(WORKFLOW)
    # Turn the top-level `return` into an exported result so Node can run it.
    wrapped = body.replace("export const meta", "const meta", 1)
    wrapped = f"export const result = await (async () => {{\n{wrapped}\n}})();\n"
    copy = tmp_path / "workflow-copy.mjs"
    copy.write_text(wrapped, encoding="utf-8")
    harness = tmp_path / "harness.mjs"
    harness.write_text(
        HARNESS
        + "\nconsole.log(JSON.stringify({ calls, result: mod.result }));\n",
        encoding="utf-8",
    )
    scenario = {
        "args": BASE_ARGS,
        "people": people or PEOPLE,
        "nullRoles": list(null_roles),
        "firstCheckProblems": list(first_check_problems),
    }
    proc = subprocess.run(
        ["node", str(harness)],
        capture_output=True,
        text=True,
        env={"SCENARIO": json.dumps(scenario), "WORKFLOW_COPY": str(copy), "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _roles(out):
    return [c["role"] for c in out["calls"]]


def test_meta_phases_match_phase_calls():
    body = _read(WORKFLOW)
    meta = body.split("export const meta", 1)[1].split("\n}\n", 1)[0]
    meta_titles = set(re.findall(r"title:\s*'([^']+)'", meta))
    called = set(re.findall(r"phase\('([^']+)'\)", body))
    assert called and called <= meta_titles


def test_one_research_agent_per_question(tmp_path):
    out = _run(tmp_path)
    assert _roles(out).count("research") == len(BASE_ARGS["research_questions"])


def test_candidate_agent_is_told_who_to_exclude(tmp_path):
    out = _run(tmp_path)
    prompt = next(c["prompt"] for c in out["calls"] if c["role"] == "candidates")
    assert "Existing Person" in prompt


def test_every_candidate_is_profiled_and_then_evaluated_by_a_separate_agent(tmp_path):
    out = _run(tmp_path)
    profiled = {n for c in out["calls"] if c["role"] == "profile" for n in PEOPLE if n in c["prompt"]}
    evaluated = {n for c in out["calls"] if c["role"] == "evaluate" for n in PEOPLE if n in c["prompt"]}
    assert profiled == set(PEOPLE)
    assert evaluated == set(PEOPLE)
    roles = _roles(out)
    assert roles.index("evaluate") > roles.index("profile")


def test_ratings_are_computed_from_cited_sources(tmp_path):
    out = _run(tmp_path)
    ratings = {e["name"]: e for e in out["result"]["evaluations"]}
    assert ratings["Ada High"]["rating"] == "High"
    assert ratings["Ada High"]["hours"] == 6.0
    assert ratings["Ben Medium"]["rating"] == "Medium"
    assert ratings["Cy Low"]["rating"] == "Low"
    # Books and talks with no URL do not count.
    assert ratings["Di Unsourced"]["rating"] == "Low"
    assert ratings["Di Unsourced"]["hours"] == 0


def test_report_is_written_then_checked_by_a_fresh_agent(tmp_path):
    out = _run(tmp_path)
    roles = _roles(out)
    assert roles.index("finalists") < roles.index("write") < roles.index("check")
    assert out["result"]["status"] == "done"


def test_problems_found_by_the_check_get_one_fix_round(tmp_path):
    out = _run(tmp_path, first_check_problems=["Ada's hours have no URL"])
    roles = _roles(out)
    assert roles.count("fix") == 1
    assert roles.count("check") == 2


def test_every_agent_prompt_points_at_a_real_prompt_section(tmp_path):
    out = _run(tmp_path)
    prompts_text = _read(PROMPTS)
    for call in out["calls"]:
        match = re.search(r'the section "(## [^"]+)"', call["prompt"])
        assert match, f"{call['role']} prompt names no section"
        assert match.group(1) in prompts_text, match.group(1)
        assert "/skill/agent-prompts.md" in call["prompt"]


def test_too_few_strong_candidates_stops_before_finalists(tmp_path):
    weak = {"Cy Low": PEOPLE["Cy Low"], "Di Unsourced": PEOPLE["Di Unsourced"]}
    out = _run(tmp_path, people=weak)
    assert out["result"]["status"] == "too_few"
    assert "finalists" not in _roles(out)


def test_a_failed_research_agent_is_reported_as_skipped(tmp_path):
    out = _run(tmp_path, null_roles=["research"])
    skipped = " ".join(out["result"]["skipped"]).lower()
    assert "research" in skipped


def test_a_failed_evaluation_is_reported_as_skipped(tmp_path):
    out = _run(tmp_path, null_roles=["evaluate"])
    skipped = " ".join(out["result"]["skipped"]).lower()
    assert "evaluat" in skipped
    assert out["result"]["status"] == "too_few"
