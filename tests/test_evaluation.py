import json
from pathlib import Path

from ptcg.evaluation import GroundTruthRegistry


def fixture(identifier: str, digest: str, *, split="evaluation", rights="APPROVED", annotation="ADJUDICATED"):
    return {
        "fixture_id": identifier,
        "content_sha256": digest,
        "source": {"kind": "synthetic-test-fixture", "provenance": "unit-test"},
        "permitted_use": "EVALUATION",
        "rights_state": rights,
        "split": split,
        "annotation_state": annotation,
        "truth": {"template_family": "pokemon", "zones": {}},
    }


def test_ground_truth_registry_qualifies_rights_and_adjudication():
    registry = GroundTruthRegistry.build(
        [
            fixture("qualified", "a" * 64),
            fixture("rights-pending", "b" * 64, rights="PENDING"),
            fixture("truth-pending", "c" * 64, annotation="ANNOTATED"),
        ]
    )
    report = registry.validate()
    assert report["status"] == "PASS"
    assert report["qualified_count"] == 1
    assert report["excluded"] == {"rights": 1, "truth": 1, "use": 0}
    assert [item["fixture_id"] for item in registry.qualified()] == ["qualified"]


def test_ground_truth_registry_detects_split_leakage():
    registry = GroundTruthRegistry.build(
        [
            fixture("train-copy", "d" * 64, split="train"),
            fixture("eval-copy", "d" * 64, split="evaluation"),
        ]
    )
    report = registry.validate()
    assert report["status"] == "FAIL"
    assert {item["code"] for item in report["findings"]} == {"SPLIT_LEAKAGE"}


def test_ground_truth_registry_round_trip(tmp_path: Path):
    registry = GroundTruthRegistry.build([fixture("one", "e" * 64)])
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry.payload), encoding="utf-8")
    assert GroundTruthRegistry.load(path).validate()["status"] == "PASS"
