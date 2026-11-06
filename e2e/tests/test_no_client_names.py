"""No tracked file names a client.

The list lives in a git-ignored file, because this plugin goes out to clients and a list of
names in a tracked file would itself name them. Each line is one name or phrase. Without the
file, the scan skips, so it runs only on a machine that holds the list.
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_LIST = Path(__file__).resolve().parent / ".client-names.local"


def _names(path: Path = LOCAL_LIST) -> list:
    if not path.exists():
        return []
    return [line.strip().lower() for line in path.read_text().splitlines() if line.strip()]


def _hits(text: str, names: list) -> list:
    lowered = text.lower()
    return [name for name in names if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", lowered)]


def _tracked_files() -> list:
    listing = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return [REPO_ROOT / name for name in listing.stdout.split("\0") if name]


def test_hits_match_whole_words_and_phrases():
    names = ["zebra", "long okapi", "a/b"]
    assert _hits("The Zebra's call.", names) == ["zebra"]
    assert _hits("A zebras call.", names) == []
    assert _hits("Some LONG OKAPI notes, and a/b.", names) == ["long okapi", "a/b"]


def test_names_are_read_and_the_list_may_be_absent(tmp_path):
    assert _names(tmp_path / "missing") == []
    listed = tmp_path / "names"
    listed.write_text("Zebra\n\n  long okapi \n")
    assert _names(listed) == ["zebra", "long okapi"]


def test_local_list_is_git_ignored():
    assert "e2e/tests/.client-names.local" in (REPO_ROOT / ".gitignore").read_text()


def test_no_tracked_file_names_a_client():
    names = _names()
    if not names:
        pytest.skip("no local client list on this machine")
    found = []
    for path in _tracked_files():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        hits = _hits(text, names)
        if hits:
            found.append(f"{path.relative_to(REPO_ROOT)}: {len(hits)} name(s)")
    assert found == []
