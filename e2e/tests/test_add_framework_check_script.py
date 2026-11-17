"""add-framework counts examples with a script, so a thin examples.md can't be reported as done.

On 2026-11-17 a run built three frameworks and reported them done. 12 of 24 phases had
fewer than two examples and five had none. The skill's rule ("2-3 examples each") was one
line of prose in Step 3. The check list in report-template.md only asked whether
examples.md existed, and the session wrote its own brief for the check agent. A count of
the plugin's own frameworks the same day found 62 of 95 with a short phase.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "add-framework"
SCRIPT = SKILL / "check_framework.py"

PROMPT = """You are Test Advisor, guiding someone through Test Method - a test.

## The Test Method Practice

### PHASE 1: Open

"What brings you here?"

**WAIT for user response before continuing.**

### PHASE 2: Middle

"Tell me more."

**WAIT for user response before continuing.**

### PHASE 3: Close

"Here is what you said."

## Artifact

A one-page summary.

## Key Rules
- Wait.
"""


def example(title):
    return f'### {title}\n\n**User:** "x"\n\n**Advisor:** "y"\n\n> Why it works\n\n'


def examples(counts):
    out = "# Test Method Examples\n\n"
    for i, n in enumerate(counts, start=1):
        out += f"## PHASE {i}: Name\n\n"
        for j in range(n):
            out += example(f"Example {i}.{j}")
    return out


def anti(n):
    out = "# Test Method Anti-Examples\n\n"
    for i in range(n):
        out += f'### Mistake {i}\n\n**User:** "x"\n\n**Wrong:** "a"\n\n**Right:** "b"\n\n> Do this.\n\n'
    return out


def build(tmp_path, counts=(2, 2, 2), anti_count=3, skip=()):
    folder = tmp_path / "test-method"
    folder.mkdir()
    files = {
        "prompt.md": PROMPT,
        "examples.md": examples(counts),
        "anti-examples.md": anti(anti_count),
        "sources.md": "PHASE 1: Open - https://example.com\n",
    }
    for name, text in files.items():
        if name not in skip:
            (folder / name).write_text(text, encoding="utf-8")
    return folder


def run(folder):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(folder)], capture_output=True, text=True
    )


# --- the script ---------------------------------------------------------------


def test_a_complete_framework_passes(tmp_path):
    result = run(build(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Problems: none" in result.stdout


def test_output_lists_the_count_for_every_phase(tmp_path):
    result = run(build(tmp_path, counts=(2, 3, 2)))
    assert "PHASE 1: 2" in result.stdout
    assert "PHASE 2: 3" in result.stdout
    assert "PHASE 3: 2" in result.stdout


def test_a_phase_with_no_examples_fails_and_is_named(tmp_path):
    result = run(build(tmp_path, counts=(2, 2, 0)))
    assert result.returncode == 1
    assert "PHASE 3 has 0 examples" in result.stdout


def test_a_phase_with_one_example_fails_and_is_named(tmp_path):
    result = run(build(tmp_path, counts=(2, 1, 2)))
    assert result.returncode == 1
    assert "PHASE 2 has 1 example" in result.stdout


def test_a_phase_missing_from_examples_counts_as_zero(tmp_path):
    result = run(build(tmp_path, counts=(2, 2)))
    assert result.returncode == 1
    assert "PHASE 3 has 0 examples" in result.stdout


def test_an_example_without_a_why_note_fails(tmp_path):
    folder = build(tmp_path)
    path = folder / "examples.md"
    path.write_text(path.read_text(encoding="utf-8").replace("> Why it works\n", "", 1), encoding="utf-8")
    result = run(folder)
    assert result.returncode == 1
    assert "no note" in result.stdout


def test_fewer_than_three_anti_examples_fails(tmp_path):
    result = run(build(tmp_path, anti_count=2))
    assert result.returncode == 1
    assert "anti-examples.md has 2 failure modes" in result.stdout


@pytest.mark.parametrize("name", ["prompt.md", "examples.md", "anti-examples.md", "sources.md"])
def test_a_missing_file_fails_and_is_named(tmp_path, name):
    result = run(build(tmp_path, skip=(name,)))
    assert result.returncode == 1
    assert name in result.stdout


def test_a_prompt_with_no_phase_headings_fails_instead_of_passing(tmp_path):
    folder = build(tmp_path)
    (folder / "prompt.md").write_text("You are X, guiding someone through Y - z.\n", encoding="utf-8")
    result = run(folder)
    assert result.returncode == 1
    assert "no phase headings" in result.stdout


def test_a_folder_that_does_not_exist_fails(tmp_path):
    result = run(tmp_path / "nope")
    assert result.returncode == 1
    assert "not a folder" in result.stdout


def test_no_folder_argument_fails_with_usage():
    result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Usage" in result.stdout


# --- the skill uses it --------------------------------------------------------


def read(name):
    return (SKILL / name).read_text(encoding="utf-8")


def test_step_3_says_every_phase_and_names_the_closing_phase():
    text = read("SKILL.md")
    three = text.split("### 3. Create examples.md")[1].split("### 4. ")[0].lower()
    assert "at least 2 examples" in three
    assert "closing phase" in three


def test_step_9_runs_the_script_before_the_check_agent():
    text = read("SKILL.md")
    nine = text.split("### 9. Check and Report")[1].split("\n## ")[0]
    assert "check_framework.py" in nine
    assert nine.index("check_framework.py") < nine.lower().index("fresh agent")
    assert "Problems: none" in nine


def test_step_9_hands_the_template_over_unchanged_and_one_agent_per_framework():
    nine = read("SKILL.md").split("### 9. Check and Report")[1].split("\n## ")[0].lower()
    assert "one agent per framework" in nine
    assert "don't write your own list" in nine


def test_check_agent_counts_by_hand_when_the_script_did_not_run():
    check = read("report-template.md").split("## Check agent")[1].split("## Report")[0]
    assert "at least 2 examples" in check
    assert "at least 3 failure modes" in check


def test_report_carries_the_scripts_output():
    report = read("report-template.md").split("## Report")[1]
    assert "check_framework.py" in report
    assert "pasted" in report.lower()


def test_anti_examples_record_the_thin_examples_run():
    text = read("anti-examples.md")
    assert "12 of 24 phases" in text
