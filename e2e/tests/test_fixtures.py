from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

EXPECTED_FIXTURES = [
    "sample-pricing-page.md",
    "sample-blog-post.md",
    "company-briefs/b2b-saas-startup.md",
]


@pytest.mark.parametrize("fixture_path", EXPECTED_FIXTURES)
def test_fixture_exists_and_is_non_empty(fixture_path):
    """Each fixture file must exist and contain content."""
    full_path = FIXTURES_DIR / fixture_path
    assert full_path.exists(), f"Fixture not found: {full_path}"
    content = full_path.read_text()
    assert len(content.strip()) > 0, f"Fixture is empty: {full_path}"
