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


def test_runner_skips_publish_for_local_file_artifact_section():
    step = section(read("skills/_shared/framework-runner.md"), "## Step 4: Publish the Result as an Artifact")
    assert "local file" in step
    assert "## Artifact" in step
    assert "nothing else in this step applies" in step


def test_add_framework_allows_local_file_result():
    skill = read("skills/add-framework/SKILL.md")
    assert "local file" in skill.split("Every framework ends with", 1)[1].split("### 3.", 1)[0]
    assert "local file" in read("skills/add-framework/report-template.md")


def test_story_map_and_breadboard_declare_local_file():
    for fw in ["user-story-map", "breadboard-to-pages"]:
        text = read(f"frameworks/{fw}/prompt.md")
        art = section(text, "\n## Artifact")
        assert "local file" in art, fw
        assert "never published" in art.lower(), fw


def test_six_step_publishes_for_itself():
    art = section(read("frameworks/6-step-process/prompt.md"), "\n## Artifact")
    assert "publishes for itself" in art
    assert "private artifact" in art
    assert "at the first write" in art
    assert "only result" in art
    assert "local file" not in art


def test_runner_lets_a_framework_publish_for_itself():
    text = read("skills/_shared/framework-runner.md")
    step = section(text, "## Step 4: Publish the Result as an Artifact")
    exception = next(line for line in step.splitlines() if "publishes for itself" in line)
    assert "## Artifact" in exception
    assert "nothing else in this step applies" in exception
    # The exception comes first, because this framework's section also names a local file.
    assert step.index("publishes for itself") < step.index("names a local file")
    assert step.index("publishes for itself") < step.index("Publish after the last phase")
    mistakes = section(text, "## Avoid These Mistakes")
    early = next(line for line in mistakes.splitlines() if "Publishing early" in line)
    assert "publishes for itself" in early
