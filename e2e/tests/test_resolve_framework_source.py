import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO
FIXTURE = REPO / "e2e" / "fixtures" / "local-advisor-repo"
MALFORMED = REPO / "e2e" / "fixtures" / "local-malformed-repo"
RESOLVER = "skills/_shared/resolve-framework-source.md"

FIRST_LINE = re.compile(r"^You are (?P<advisor>.+?), guiding someone through (?P<name>.+?) - ")


def read(rel):
    return (REPO / rel).read_text()


def _scoped(entry, root, source, registered=True):
    entry = dict(entry)
    fdir = root / "frameworks" / entry["id"]
    entry["absolute_framework_dir"] = fdir
    entry["absolute_prompt_path"] = fdir / "prompt.md"
    entry["source"] = source
    entry["registered"] = registered
    return entry


def _parse_first_line(prompt_path):
    """Return (advisor, name) from the 'You are ...' line, skipping frontmatter."""
    for line in prompt_path.read_text().splitlines():
        m = FIRST_LINE.match(line)
        if m:
            return m.group("advisor"), m.group("name")
    return None, None


def merge_frameworks(plugin_root, project_root):
    """Oracle for the procedure in skills/_shared/resolve-framework-source.md.

    Returns (entries, warnings). Test-only.
    """
    plugin_data = yaml.safe_load((plugin_root / "frameworks" / "registry.yaml").read_text())
    merged = {}
    for e in plugin_data["frameworks"]:
        merged[e["id"]] = _scoped(e, plugin_root, "plugin")
    warnings = []

    if project_root.resolve() == plugin_root.resolve():
        return list(merged.values()), warnings

    local_ids = set()
    local_registry = project_root / "frameworks" / "registry.yaml"
    if local_registry.is_file():
        try:
            local_data = yaml.safe_load(local_registry.read_text())
            for e in (local_data or {}).get("frameworks", []):
                merged[e["id"]] = _scoped(e, project_root, "local")
                local_ids.add(e["id"])
        except yaml.YAMLError:
            warnings.append(
                f"Warning: could not parse {local_registry}; using plugin frameworks only."
            )

    for prompt in sorted((project_root / "frameworks").glob("*/prompt.md")):
        folder = prompt.parent.name
        if folder in local_ids:
            continue
        advisor, name = _parse_first_line(prompt)
        entry = {
            "id": folder,
            "name": name or folder,
            "advisor": advisor or "",
            "purpose": "",
            "category": "",
            "domains": [],
            "use_when": "",
        }
        merged[folder] = _scoped(entry, project_root, "local", registered=False)

    return list(merged.values()), warnings


def find_advisor(merged_advisors, key):
    """Match by id first, then by display name (case-insensitive). None if no match."""
    for source, a in merged_advisors:
        if a["id"] == key:
            return source, a
    for source, a in merged_advisors:
        if a["name"].lower() == key.lower():
            return source, a
    return None


def _merged_advisors():
    plugin = yaml.safe_load((PLUGIN / "advisors" / "registry.yaml").read_text())["advisors"]
    local = yaml.safe_load((FIXTURE / "advisors" / "registry.yaml").read_text())["advisors"]
    by_id = {a["id"]: ("plugin", a) for a in plugin}
    by_id.update({a["id"]: ("local", a) for a in local})
    return list(by_id.values())


def _plugin_ids():
    data = yaml.safe_load((PLUGIN / "frameworks" / "registry.yaml").read_text())
    return [e["id"] for e in data["frameworks"]]


def _by_id(entries):
    return {e["id"]: e for e in entries}


# ---- Text tests on the resolver ----


def test_resolver_file_exists():
    assert (REPO / RESOLVER).is_file()


def test_resolver_documents_plugin_canonical_then_local_merge():
    text = read(RESOLVER)
    assert "canonical" in text.lower()
    assert "registry.yaml" in text
    assert "<project-cwd>/frameworks/registry.yaml" in text


def test_resolver_documents_dedupe_before_return_local_wins():
    text = read(RESOLVER).lower()
    assert "dedupe" in text or "deduplicate" in text
    assert "before return" in text or "before returning" in text
    assert "local-wins" in text or "local wins" in text


def test_resolver_documents_scope_roots():
    text = read(RESOLVER)
    for term in ["plugin-root", "project-cwd", "absolute_framework_dir", "absolute_prompt_path"]:
        assert term in text, f"resolver must name: {term}"


def test_resolver_documents_glob_for_unregistered_local_folders():
    text = read(RESOLVER)
    assert "frameworks/*/prompt.md" in text
    assert "registered" in text


def test_resolver_documents_error_paths():
    text = read(RESOLVER).lower()
    assert "absent" in text and "plugin-only" in text
    assert "malformed" in text and "warning" in text
    assert "frameworks/registry.yaml" in text  # the warning names the file
    assert "warning: could not parse" in text
    assert "fail closed" in text or "fails closed" in text or "fail-close" in text


def test_resolver_documents_return_contract():
    text = read(RESOLVER)
    for field in [
        "id", "name", "advisor", "purpose", "category", "domains", "use_when",
        "deliverable_type", "default_critic_advisors", "required_documents",
        "helpful_documents", "absolute_framework_dir", "absolute_prompt_path",
        "source", "registered",
    ]:
        assert field in text, f"return contract must name field: {field}"
    assert "plugin | local" in text or '"plugin"' in text


def test_resolver_points_advisor_lookup_at_resolve_advisor_source():
    text = read(RESOLVER)
    assert "skills/_shared/resolve-advisor-source.md" in text


def test_resolver_is_in_eval_surface():
    assert RESOLVER in read("e2e/eval-surface.yaml"), (
        "new LLM behavior surface must be listed in eval-surface.yaml"
    )


# ---- Oracle tests ----


def test_merge_with_no_local_registry_is_plugin_only(tmp_path):
    entries, warnings = merge_frameworks(PLUGIN, tmp_path)
    assert [e["id"] for e in entries] == _plugin_ids()
    assert all(e["source"] == "plugin" for e in entries)
    assert warnings == []


def test_merge_with_local_registry_adds_local_entries():
    entries, warnings = merge_frameworks(PLUGIN, FIXTURE)
    entry = _by_id(entries)["example-local-framework"]
    assert entry["source"] == "local"
    assert entry["absolute_prompt_path"] == FIXTURE / "frameworks/example-local-framework/prompt.md"
    assert warnings == []


def test_merge_local_wins_on_duplicate_id():
    entries, _ = merge_frameworks(PLUGIN, FIXTURE)
    matches = [e for e in entries if e["id"] == "fear-setting"]
    assert len(matches) == 1
    assert matches[0]["source"] == "local"
    assert matches[0]["name"] == "Fear Setting (local override)"
    assert FIXTURE in matches[0]["absolute_prompt_path"].parents


def test_merge_malformed_local_yaml_degrades_with_warning():
    entries, warnings = merge_frameworks(PLUGIN, MALFORMED)
    assert [e["id"] for e in entries] == _plugin_ids()
    assert all(e["source"] == "plugin" for e in entries)
    assert len(warnings) == 1
    assert "frameworks/registry.yaml" in warnings[0]


def test_merge_finds_unregistered_local_folder_by_glob():
    entries, _ = merge_frameworks(PLUGIN, FIXTURE)
    entry = _by_id(entries)["unregistered-local-framework"]
    assert entry["registered"] is False
    assert entry["source"] == "local"
    assert entry["name"] == "Unregistered Local Framework"
    assert entry["advisor"] == "Example Local Advisor"


def test_local_framework_advisor_resolves_in_merged_advisors():
    plugin_advisors = yaml.safe_load((PLUGIN / "advisors" / "registry.yaml").read_text())["advisors"]
    local_advisors = yaml.safe_load((FIXTURE / "advisors" / "registry.yaml").read_text())["advisors"]
    merged = {a["id"]: ("plugin", a) for a in plugin_advisors}
    merged.update({a["id"]: ("local", a) for a in local_advisors})

    entries, _ = merge_frameworks(PLUGIN, FIXTURE)
    framework = _by_id(entries)["example-local-framework"]
    source, advisor = merged[framework["advisor"]]
    assert source == "local"
    assert (FIXTURE / "advisors/prompts" / f"{advisor['id']}.md").is_file()


def test_unregistered_framework_advisor_resolves_by_name():
    entries, _ = merge_frameworks(PLUGIN, FIXTURE)
    framework = _by_id(entries)["unregistered-local-framework"]
    source, advisor = find_advisor(_merged_advisors(), framework["advisor"])
    assert source == "local"
    assert advisor["id"] == "example-local-advisor"


def test_advisor_lookup_with_no_match_returns_none():
    assert find_advisor(_merged_advisors(), "Nobody At All") is None


def test_unregistered_folder_without_header_uses_folder_name():
    entries, _ = merge_frameworks(PLUGIN, FIXTURE)
    entry = _by_id(entries)["no-header-local-framework"]
    assert entry["registered"] is False
    assert entry["name"] == "no-header-local-framework"
    assert entry["advisor"] == ""
    assert find_advisor(_merged_advisors(), entry["advisor"]) is None


def test_unregistered_entries_have_empty_purpose_category_domains_use_when():
    entries, _ = merge_frameworks(PLUGIN, FIXTURE)
    for fid in ["unregistered-local-framework", "no-header-local-framework"]:
        e = _by_id(entries)[fid]
        assert e["purpose"] == "" and e["category"] == ""
        assert e["domains"] == [] and e["use_when"] == ""


def test_docs_say_projects_keep_local_registries():
    for doc in ["CLAUDE.md", "README.md"]:
        text = read(doc)
        assert "frameworks/registry.yaml" in text, doc
        assert "advisors/registry.yaml" in text, doc
        assert "project root" in text, doc
        assert "merge" in text, doc
        assert "local entry wins" in text, doc
    claude = read("CLAUDE.md")
    assert "resolve-advisor-source" in claude
    assert "resolve-framework-source" in claude
