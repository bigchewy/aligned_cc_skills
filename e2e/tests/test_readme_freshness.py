"""Guard the markdown READMEs against the staleness that motivated their regeneration:
headline counts must match the registries, and no migrated/phantom advisor id may appear."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]

GONE_IDS = [
    "benjamin-levine", "copywriter",
    "andreo-spina", "blair-grubb", "italo-biaggioni", "kelly-starrett",
    "patrick-mckeown", "roy-freeman", "shirley-sahrmann", "stuart-mcgill",
    "deb-dana", "irene-lyon", "akiko-iwasaki", "david-putrino", "david-systrom",
    "byron-katie", "gabor-mate", "marsha-linehan", "martin-seligman",
    "richard-schwartz", "steven-hayes",
    # phantom framework IDs — benjamin-levine's 4 frameworks (folders already absent, still in README)
    "autonomic-fatigue-vs-training-fatigue", "cardiac-deconditioning-model",
    "heart-rate-reserve-training-zones", "levine-protocol",
]


def _count(rel, key):
    with open(REPO / rel) as f:
        return len(yaml.safe_load(f)[key])


def test_advisor_readme_headline_count_matches_registry():
    n = _count("advisors/registry.yaml", "advisors")
    text = (REPO / "advisors" / "README.md").read_text()
    assert str(n) in text.splitlines()[2], f"advisors/README.md headline must show {n} advisors"


def test_framework_readme_headline_count_matches_registry():
    n = _count("frameworks/registry.yaml", "frameworks")
    text = (REPO / "frameworks" / "README.md").read_text()
    assert str(n) in text.splitlines()[2], f"frameworks/README.md headline must show {n} frameworks"


def test_readmes_drop_migrated_and_phantom_ids():
    adv = (REPO / "advisors" / "README.md").read_text()
    fw = (REPO / "frameworks" / "README.md").read_text()
    for gid in GONE_IDS:
        assert gid not in adv, f"advisors/README.md still references migrated/phantom id: {gid}"
        assert gid not in fw, f"frameworks/README.md still references migrated/phantom id: {gid}"
