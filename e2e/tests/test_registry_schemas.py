# e2e/tests/test_registry_schemas.py

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ADVISOR_REQUIRED_FIELDS = {"id", "name", "summary", "prompt", "domains"}
FRAMEWORK_REQUIRED_FIELDS = {"id", "name", "advisor", "purpose", "category", "domains", "use_when"}


def _load_outliers():
    """Shared source of truth for outlier frameworks, also read by generate-framework-registry.mjs."""
    with open(REPO_ROOT / "frameworks" / "_outliers.json") as f:
        return json.load(f)["outliers"]


OUTLIER_PARAMS = [
    (slug, meta["name"], meta["advisor"])
    for slug, meta in _load_outliers().items()
]


class TestAdvisorRegistrySchema:
    """Validates advisors/registry.yaml structure and required fields."""

    @pytest.fixture
    def registry(self):
        path = REPO_ROOT / "advisors" / "registry.yaml"
        assert path.exists(), f"Advisor registry not found at {path}"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data is not None, "Advisor registry is empty"
        return data

    def test_has_advisors_list(self, registry):
        assert "advisors" in registry, "Missing top-level 'advisors' key"
        assert isinstance(registry["advisors"], list), "'advisors' must be a list"
        assert len(registry["advisors"]) > 0, "Advisors list is empty"

    def test_has_selection_guidelines(self, registry):
        assert "selection_guidelines" in registry, "Missing 'selection_guidelines' key"

    def test_all_entries_have_required_fields(self, registry):
        for i, entry in enumerate(registry["advisors"]):
            missing = ADVISOR_REQUIRED_FIELDS - set(entry.keys())
            assert not missing, (
                f"Advisor entry {i} ({entry.get('id', 'unknown')}) "
                f"missing required fields: {missing}"
            )

    def test_domains_is_list(self, registry):
        for entry in registry["advisors"]:
            assert isinstance(entry["domains"], list), (
                f"Advisor {entry['id']}: 'domains' must be a list, "
                f"got {type(entry['domains']).__name__}"
            )

    def test_prompt_paths_exist(self, registry):
        for entry in registry["advisors"]:
            prompt_path = REPO_ROOT / entry["prompt"]
            assert prompt_path.exists(), (
                f"Advisor {entry['id']}: prompt file not found at {entry['prompt']}"
            )

    def test_ids_are_unique(self, registry):
        ids = [e["id"] for e in registry["advisors"]]
        dupes = [x for x in ids if ids.count(x) > 1]
        assert not dupes, f"Duplicate advisor IDs: {set(dupes)}"

    def test_entry_count_matches_prompts(self, registry):
        prompt_dir = REPO_ROOT / "advisors" / "prompts"
        prompt_files = list(prompt_dir.glob("*.md"))
        registry_count = len(registry["advisors"])
        file_count = len(prompt_files)
        assert registry_count == file_count, (
            f"Registry has {registry_count} entries but "
            f"advisors/prompts/ has {file_count} .md files"
        )


class TestFrameworkRegistrySchema:
    """Validates frameworks/registry.yaml structure and required fields."""

    @pytest.fixture
    def registry(self):
        path = REPO_ROOT / "frameworks" / "registry.yaml"
        assert path.exists(), f"Framework registry not found at {path}"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data is not None, "Framework registry is empty"
        return data

    def test_has_frameworks_list(self, registry):
        assert "frameworks" in registry, "Missing top-level 'frameworks' key"
        assert isinstance(registry["frameworks"], list), "'frameworks' must be a list"
        assert len(registry["frameworks"]) > 0, "Frameworks list is empty"

    def test_all_entries_have_required_fields(self, registry):
        for i, entry in enumerate(registry["frameworks"]):
            missing = FRAMEWORK_REQUIRED_FIELDS - set(entry.keys())
            assert not missing, (
                f"Framework entry {i} ({entry.get('id', 'unknown')}) "
                f"missing required fields: {missing}"
            )

    def test_purpose_is_non_empty(self, registry):
        for entry in registry["frameworks"]:
            purpose = entry.get("purpose", "")
            assert isinstance(purpose, str) and purpose.strip(), (
                f"Framework {entry['id']}: 'purpose' must be a non-empty string, "
                f"got {purpose!r}"
            )

    def test_use_when_is_non_empty(self, registry):
        for entry in registry["frameworks"]:
            use_when = entry.get("use_when", "")
            assert isinstance(use_when, str) and use_when.strip(), (
                f"Framework {entry['id']}: 'use_when' must be a non-empty string, "
                f"got {use_when!r}"
            )

    def test_domains_is_list(self, registry):
        for entry in registry["frameworks"]:
            assert isinstance(entry["domains"], list), (
                f"Framework {entry['id']}: 'domains' must be a list, "
                f"got {type(entry['domains']).__name__}"
            )

    def test_ids_are_unique(self, registry):
        ids = [e["id"] for e in registry["frameworks"]]
        dupes = [x for x in ids if ids.count(x) > 1]
        assert not dupes, f"Duplicate framework IDs: {set(dupes)}"

    def test_entry_count_matches_directories(self, registry):
        fw_dir = REPO_ROOT / "frameworks"
        fw_dirs = [
            d for d in fw_dir.iterdir()
            if d.is_dir() and (d / "prompt.md").exists()
        ]
        registry_count = len(registry["frameworks"])
        dir_count = len(fw_dirs)
        assert registry_count == dir_count, (
            f"Registry has {registry_count} entries but "
            f"frameworks/ has {dir_count} directories with prompt.md"
        )

    def test_name_field_is_concise(self, registry):
        """Framework name fields must be concise (≤60 chars) — they surface to users in pickers."""
        long_names = [
            (e["id"], len(e["name"]))
            for e in registry["frameworks"]
            if len(e["name"]) > 60
        ]
        assert not long_names, (
            f"{len(long_names)} entries have name > 60 chars: {long_names[:5]}"
        )

    @pytest.mark.parametrize("slug,expected_name,expected_advisor", OUTLIER_PARAMS)
    def test_outlier_frameworks_have_correct_metadata(self, registry, slug, expected_name, expected_advisor):
        """Outlier frameworks (defined in frameworks/_outliers.json) must have correct name and advisor."""
        entry = next((e for e in registry["frameworks"] if e["id"] == slug), None)
        assert entry is not None, f"Outlier framework {slug} not found in registry"
        assert entry["name"] == expected_name, (
            f"Framework {slug}: expected name '{expected_name}', got '{entry['name']}'"
        )
        assert entry["advisor"] == expected_advisor, (
            f"Framework {slug}: expected advisor '{expected_advisor}', got '{entry['advisor']}'"
        )

    def test_registry_documents_deliverable_type_taxonomy(self):
        with open(REPO_ROOT / "frameworks" / "registry.yaml") as f:
            head = f.read(2000)
        for tag in ["content", "decision", "plan", "analysis"]:
            assert tag in head, f"deliverable_type taxonomy must document tag: {tag}"
        assert "deliverable_type" in head, "missing taxonomy doc block"
