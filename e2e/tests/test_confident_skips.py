"""Skills decide what they can, ask only what they can't, and say what they decided.

The user's rule (2026-10-28): a skill may skip a question when it is highly confident
of the answer, never on a significant guess, and should not ask what it already knows.

- root-cause-analysis never made its severity call. With no argument it ran low:
  no agents, and no check. One real run of a strategy problem across three people
  (two of the skill's own high-severity signals) missed a concern from the source.
- brainstorming always asked for the mode. In one real run Claude wrote "roadmap mode:"
  into its own arguments for a request that wanted advisors and an Asana plan. Roadmap
  mode excludes advisors, so it then ignored the mode's rules without saying so.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def section(text, heading):
    assert heading in text, f"missing {heading}"
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


# --- root-cause-analysis ---------------------------------------------------------


def test_rca_picks_severity_from_its_own_criteria():
    s = section(read("skills/root-cause-analysis/SKILL.md"), "## Severity Levels").lower()
    assert "default severity is **low**" not in s
    assert "pick the severity yourself" in s
    assert "when to use high severity" in s
    assert "say which" in s
    assert "ask only when" in s


def test_rca_description_does_not_promise_a_low_default():
    front = read("skills/root-cause-analysis/SKILL.md").split("---", 2)[1]
    assert "low (default)" not in front


def test_rca_checks_analysis_only_runs_for_missed_items():
    text = read("skills/root-cause-analysis/SKILL.md")
    s = section(text, "## Analysis-Only Review").lower()
    assert "fresh agent" in s
    assert "source" in s
    assert "missed" in s


# --- brainstorming ---------------------------------------------------------------


def test_brainstorming_no_longer_always_asks():
    text = read("skills/brainstorming/SKILL.md")
    assert "**Always ask the user to confirm.**" not in text
    s = text.lower()
    assert "highly confident" in s
    assert "say the mode" in s


def test_brainstorming_checks_the_mode_fits_the_request():
    s = read("skills/brainstorming/SKILL.md").lower()
    assert "excludes" in s
    assert "follow its rules" in s


def test_routing_eval_matches_the_new_rule():
    text = read("e2e/scenarios/use-skill/always-ask-routing.yaml")
    assert "always presents picker = 5" not in text
    assert "clear single-mode request" in text.lower()
