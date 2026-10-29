"""Every framework ends by publishing its result as an artifact in the project's brand.

The user asked on 2026-10-28 that frameworks always create a Claude Artifact that uses
the design principles. Before this, no runner, skill or framework prompt published one.
The rule lives in the framework runner so all frameworks get it. The design-principles
lookup moves to its own shared file so visualizations and framework artifacts use the
same one.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def section(text, heading):
    assert heading in text, f"missing {heading}"
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def test_design_principles_lookup_is_a_shared_file():
    text = read("skills/_shared/resolve-design-principles.md")
    for step in [
        "docs/design/design-principles.md",
        "apps/*/docs/design/design-principles.md",
        "~/.claude/docs/design/design-principles.md",
    ]:
        assert step in text, step
    assert "placeholder" in text.lower()
    assert "500 bytes" in text


def test_visualization_runner_uses_the_shared_lookup():
    text = read("skills/_shared/visualization-runner.md")
    assert "skills/_shared/resolve-design-principles.md" in text


def test_framework_runner_publishes_an_artifact_at_the_end():
    text = read("skills/_shared/framework-runner.md")
    step = section(text, "## Step 4: Publish the Result as an Artifact")
    assert "skills/_shared/resolve-design-principles.md" in step
    assert "Artifact tool" in step
    assert "artifact-design" in step
    # Built from the session, after the last phase, never before a WAIT.
    assert "user's own answers" in step
    assert "last phase" in step


def test_framework_runner_falls_back_to_a_file_without_the_artifact_tool():
    step = section(read("skills/_shared/framework-runner.md"), "## Step 4: Publish the Result as an Artifact")
    assert "HTML file" in step
    assert "docs/frameworks/" in step


def test_framework_runner_lets_a_caller_turn_the_artifact_off():
    text = read("skills/_shared/framework-runner.md")
    assert "`publish_artifact`" in section(text, "## Configuration")
    authoring = read("skills/brainstorming/modes/authoring.md")
    assert "`publish_artifact`:** `no`" in authoring


def test_add_framework_requires_an_artifact_section():
    text = read("skills/add-framework/SKILL.md")
    assert "## Artifact" in text
    check = read("skills/add-framework/report-template.md")
    assert "## Artifact" in check
