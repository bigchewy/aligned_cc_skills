from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_resolver_file_exists():
    assert (REPO / "skills/_shared/resolve-advisor-source.md").is_file()


def test_resolver_documents_merge_order_plugin_canonical():
    text = read("skills/_shared/resolve-advisor-source.md")
    assert "canonical" in text.lower()
    assert "plugin" in text.lower() and "registry.yaml" in text


def test_resolver_documents_dedupe_before_return_local_wins():
    text = read("skills/_shared/resolve-advisor-source.md").lower()
    assert "dedupe" in text or "deduplicate" in text
    assert "before return" in text or "before returning" in text
    assert "local-wins" in text or "local wins" in text


def test_resolver_documents_scope_root_derivation():
    text = read("skills/_shared/resolve-advisor-source.md")
    # plugin entries anchor on plugin-root; local entries on project-cwd
    assert "plugin-root" in text or "plugin root" in text
    assert "project-cwd" in text or "project cwd" in text
    assert "absolute_prompt_path" in text


def test_resolver_documents_prompt_dir_override_and_default():
    text = read("skills/_shared/resolve-advisor-source.md")
    assert "advisors/prompts" in text  # the default
    assert "prompt-dir" in text or "prompt dir" in text or "<prompt-dir>" in text
    assert "CLAUDE.md" in text  # the override source


def test_resolver_documents_ignore_prompt_field():
    text = read("skills/_shared/resolve-advisor-source.md").lower()
    assert "ignored for resolution" in text


def test_resolver_documents_selection_guidelines_plugin_canonical():
    text = read("skills/_shared/resolve-advisor-source.md")
    assert "selection_guidelines" in text
    # local repos do not override panel selection rules
    assert "plugin" in text.lower()


def test_resolver_documents_four_error_paths():
    text = read("skills/_shared/resolve-advisor-source.md").lower()
    assert "absent" in text or "does not exist" in text  # local registry absent -> plugin-only
    assert "malformed" in text and "warning" in text     # malformed local -> degrade + warn
    assert "default" in text                              # prompt-dir override absent -> default
    assert "fail-close" in text or "fail closed" in text or "use time" in text  # missing prompt file


def test_resolver_documents_return_contract():
    text = read("skills/_shared/resolve-advisor-source.md")
    for field in ["id", "name", "absolute_prompt_path", "source"]:
        assert field in text, f"return contract must name field: {field}"
    assert '"plugin"' in text or "plugin | local" in text or '"local"' in text


def test_resolver_is_in_eval_surface():
    text = read("e2e/eval-surface.yaml")
    assert "skills/_shared/resolve-advisor-source.md" in text, (
        "new LLM behavior surface must be listed in eval-surface.yaml"
    )
