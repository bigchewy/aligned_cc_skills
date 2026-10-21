from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_use_framework_step1_routes_through_resolver():
    text = read("skills/use-framework/SKILL.md")
    assert "skills/_shared/resolve-framework-source.md" in text


def test_use_framework_marks_local_frameworks():
    text = read("skills/use-framework/SKILL.md")
    assert "(local)" in text
    assert 'source: "local"' in text


def test_use_framework_passes_merged_list_to_recommendation():
    text = read("skills/use-framework/SKILL.md")
    assert "registry path: `frameworks/registry.yaml`" not in text
    assert "pre-merged" in text.lower()


def test_use_framework_runner_path_is_absolute_framework_dir():
    text = read("skills/use-framework/SKILL.md")
    assert "absolute_framework_dir" in text
    assert "<plugin-root>/frameworks/<id>/" not in text


def test_use_framework_first_line_parse_only_for_unregistered():
    text = read("skills/use-framework/SKILL.md")
    step2 = text.split("## Step 2", 1)[1].split("## Step 3", 1)[0]
    assert "registered: false" in step2
    assert "only" in step2


def _step2(text):
    return text.split("## Step 2", 1)[1].split("## Step 3", 1)[0]


def test_use_framework_step2_has_list_all_paragraph():
    step2 = _step2(read("skills/use-framework/SKILL.md"))
    assert "List all" in step2
    assert "list all" in step2.lower()
    assert "Step 1a" in step2


def test_use_framework_list_all_puts_local_first_with_marker():
    step2 = _step2(read("skills/use-framework/SKILL.md"))
    assert "first" in step2
    assert "own heading" in step2
    assert "(local)" in step2
    assert "alphabetically" in step2


def test_use_framework_list_all_never_shortens_local_group():
    step2 = _step2(read("skills/use-framework/SKILL.md"))
    assert "Never shorten or summarize the local group" in step2


def test_use_framework_bare_call_without_context_lists():
    text = read("skills/use-framework/SKILL.md")
    step3 = text.split("## Step 3", 1)[1].split("## Step 4", 1)[0]
    assert "no task" in step3.lower()
    assert "List all" in step3
    # invocation line says the same thing
    inv = text.split("## Invocation", 1)[1].split("## Step 1", 1)[0]
    assert "no task" in inv.lower()
