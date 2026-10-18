import json
from pathlib import Path

from ptcg.evaluation import (
    GroundTruthRegistry,
    score_template_classification,
    score_zone_localization,
)


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


def test_template_scorecard_reports_top_k_subtype_abstention_and_sparse_strata():
    first = fixture("one", "1" * 64)
    first["truth"].update(template_family="pokemon", template_subtype="modern", stratum="en-modern")
    second = fixture("two", "2" * 64)
    second["truth"].update(template_family="trainer", template_subtype="item", stratum="en-modern")
    registry = GroundTruthRegistry.build([first, second])
    scorecard = score_template_classification(
        registry,
        [
            {"fixture_id": "one", "family_top_k": ["pokemon", "trainer"], "selected_family": "pokemon", "selected_subtype": "modern", "abstained": False},
            {"fixture_id": "two", "family_top_k": ["pokemon", "trainer"], "selected_family": None, "selected_subtype": None, "abstained": True},
        ],
        top_k=2,
        minimum_stratum_size=5,
        template_registry_version="sha256:" + "f" * 64,
    )
    assert scorecard["family_top_k_recall"] == 1.0
    assert scorecard["subtype_accuracy"] == 0.5
    assert scorecard["abstention_rate"] == 0.5
    assert scorecard["confusion"]["trainer"]["ABSTAIN"] == 1
    assert scorecard["strata"]["en-modern"]["evidence_state"] == "EVIDENCE_REQUIRED"
    assert scorecard["calibration_state"] == "UNCALIBRATED"


def test_zone_scorecard_separates_presence_geometry_and_status():
    item = fixture("zones", "3" * 64)
    item["truth"].update(
        template_stratum="pokemon-modern",
        zones={
            "title": {"present": True, "zone_type": "text", "rect": [0.0, 0.0, 0.5, 0.2]},
            "set_symbol": {"present": True, "zone_type": "symbol", "keypoint": [0.8, 0.8]},
            "absent_rule": {"present": False, "zone_type": "rule_box"},
        },
    )
    registry = GroundTruthRegistry.build([item])
    scorecard = score_zone_localization(
        registry,
        [
            {
                "fixture_id": "zones",
                "zones": {
                    "title": {"present": True, "status": "INDEPENDENTLY_LOCALIZED", "rect": [0.0, 0.0, 0.5, 0.2]},
                    "set_symbol": {"present": True, "status": "FALLBACK_USED", "keypoint": [0.82, 0.81]},
                    "absent_rule": {"present": True, "status": "INHERITED_PRIOR"},
                },
            }
        ],
        minimum_stratum_size=2,
        keypoint_tolerance=0.05,
    )
    assert scorecard["presence_precision"] == 2 / 3
    assert scorecard["presence_recall"] == 1.0
    assert scorecard["mean_iou"] == 1.0
    assert scorecard["keypoint_accuracy"] == 1.0
    assert scorecard["localization_status_counts"]["FALLBACK_USED"] == 1
    assert scorecard["strata"]["pokemon-modern/symbol"]["evidence_state"] == "EVIDENCE_REQUIRED"
