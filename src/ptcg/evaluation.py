from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .util import canonical_json_sha256


SPLITS = {"train", "development", "evaluation"}
PERMITTED_USES = {"TRAINING", "DEVELOPMENT", "EVALUATION"}


@dataclass(frozen=True)
class GroundTruthRegistry:
    payload: dict[str, Any]

    @classmethod
    def load(cls, path: Path) -> "GroundTruthRegistry":
        value = json.loads(path.resolve(strict=True).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("ground-truth registry must be a JSON object")
        return cls(value)

    @classmethod
    def build(cls, fixtures: list[dict[str, Any]]) -> "GroundTruthRegistry":
        body = {
            "schema_version": "ground-truth-registry-v1",
            "fixtures": fixtures,
        }
        body["registry_id"] = f"sha256:{canonical_json_sha256(body)}"
        return cls(body)

    def validate(self) -> dict[str, Any]:
        findings: list[dict[str, str]] = []
        fixtures = self.payload.get("fixtures")
        if not isinstance(fixtures, list):
            fixtures = []
            findings.append(_finding("FIXTURES_INVALID", "fixtures must be an array"))
        unsigned = {key: value for key, value in self.payload.items() if key != "registry_id"}
        expected = f"sha256:{canonical_json_sha256(unsigned)}"
        if self.payload.get("registry_id") != expected:
            findings.append(_finding("REGISTRY_ID_MISMATCH", "registry identity is invalid"))
        fixture_ids: set[str] = set()
        digest_splits: dict[str, set[str]] = {}
        excluded = {"rights": 0, "truth": 0, "use": 0}
        for index, fixture in enumerate(fixtures):
            if not isinstance(fixture, dict):
                findings.append(_finding("FIXTURE_INVALID", f"fixture {index} is not an object"))
                continue
            fixture_id = fixture.get("fixture_id")
            digest = fixture.get("content_sha256")
            split = fixture.get("split")
            if not isinstance(fixture_id, str) or not fixture_id:
                findings.append(_finding("FIXTURE_ID_INVALID", f"fixture {index} has no identity"))
            elif fixture_id in fixture_ids:
                findings.append(_finding("FIXTURE_ID_DUPLICATE", fixture_id))
            else:
                fixture_ids.add(fixture_id)
            if not isinstance(digest, str) or len(digest) != 64:
                findings.append(_finding("CONTENT_DIGEST_INVALID", str(fixture_id)))
            if split not in SPLITS:
                findings.append(_finding("SPLIT_INVALID", str(fixture_id)))
            elif isinstance(digest, str):
                digest_splits.setdefault(digest, set()).add(split)
            if fixture.get("rights_state") != "APPROVED":
                excluded["rights"] += 1
            if fixture.get("annotation_state") != "ADJUDICATED":
                excluded["truth"] += 1
            if fixture.get("permitted_use") not in PERMITTED_USES:
                excluded["use"] += 1
        for digest, splits in digest_splits.items():
            if len(splits) > 1:
                findings.append(
                    _finding(
                        "SPLIT_LEAKAGE",
                        f"sha256:{digest} occurs across {sorted(splits)}",
                    )
                )
        return {
            "registry_id": self.payload.get("registry_id"),
            "status": "PASS" if not findings else "FAIL",
            "fixture_count": len(fixtures),
            "qualified_count": len(self.qualified()),
            "excluded": excluded,
            "findings": findings,
        }

    def qualified(self, *, split: str | None = None, permitted_use: str | None = None) -> list[dict[str, Any]]:
        result = []
        for fixture in self.payload.get("fixtures", []):
            if not isinstance(fixture, dict):
                continue
            if fixture.get("rights_state") != "APPROVED":
                continue
            if fixture.get("annotation_state") != "ADJUDICATED":
                continue
            if fixture.get("permitted_use") not in PERMITTED_USES:
                continue
            if split is not None and fixture.get("split") != split:
                continue
            if permitted_use is not None and fixture.get("permitted_use") != permitted_use:
                continue
            result.append(fixture)
        return result


def _finding(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def score_template_classification(
    registry: GroundTruthRegistry,
    predictions: list[dict[str, Any]],
    *,
    split: str = "evaluation",
    top_k: int = 3,
    minimum_stratum_size: int = 5,
    template_registry_version: str,
) -> dict[str, Any]:
    """Measure ranked template hypotheses without treating scores as calibrated."""
    fixtures = registry.qualified(split=split, permitted_use="EVALUATION")
    by_id = {item["fixture_id"]: item for item in fixtures}
    prediction_by_id = {item["fixture_id"]: item for item in predictions}
    evaluated = 0
    family_hits = 0
    subtype_hits = 0
    subtype_total = 0
    abstentions = 0
    confusion: dict[str, dict[str, int]] = {}
    strata: dict[str, dict[str, int]] = {}
    missing: list[str] = []
    for fixture_id, fixture in by_id.items():
        prediction = prediction_by_id.get(fixture_id)
        if prediction is None:
            missing.append(fixture_id)
            continue
        truth = fixture.get("truth", {})
        expected_family = truth.get("template_family")
        expected_subtype = truth.get("template_subtype")
        ranked = prediction.get("family_top_k", [])[:top_k]
        selected_family = prediction.get("selected_family")
        selected_subtype = prediction.get("selected_subtype")
        abstained = bool(prediction.get("abstained"))
        evaluated += 1
        family_hits += int(expected_family in ranked)
        abstentions += int(abstained)
        observed = "ABSTAIN" if abstained else str(selected_family)
        confusion.setdefault(str(expected_family), {})[observed] = (
            confusion.setdefault(str(expected_family), {}).get(observed, 0) + 1
        )
        if expected_subtype is not None:
            subtype_total += 1
            subtype_hits += int(selected_subtype == expected_subtype)
        stratum = str(truth.get("stratum", expected_family or "UNKNOWN"))
        bucket = strata.setdefault(stratum, {"count": 0, "family_top_k_hits": 0})
        bucket["count"] += 1
        bucket["family_top_k_hits"] += int(expected_family in ranked)
    stratum_results = {}
    for name, bucket in sorted(strata.items()):
        count = bucket["count"]
        stratum_results[name] = {
            **bucket,
            "family_top_k_recall": bucket["family_top_k_hits"] / count,
            "evidence_state": (
                "MEASURED" if count >= minimum_stratum_size else "EVIDENCE_REQUIRED"
            ),
        }
    return {
        "schema_version": "template-classification-scorecard-v1",
        "registry_id": registry.payload.get("registry_id"),
        "fixture_split": split,
        "template_registry_version": template_registry_version,
        "top_k": top_k,
        "evaluated": evaluated,
        "missing_predictions": sorted(missing),
        "family_top_k_recall": family_hits / evaluated if evaluated else None,
        "subtype_accuracy": subtype_hits / subtype_total if subtype_total else None,
        "abstention_rate": abstentions / evaluated if evaluated else None,
        "confusion": confusion,
        "strata": stratum_results,
        "calibration_state": "UNCALIBRATED",
        "claim_state": "EVIDENCE_REQUIRED" if missing or not evaluated else "MEASURED",
    }


def score_zone_localization(
    registry: GroundTruthRegistry,
    predictions: list[dict[str, Any]],
    *,
    split: str = "evaluation",
    minimum_stratum_size: int = 5,
    keypoint_tolerance: float = 0.05,
) -> dict[str, Any]:
    fixtures = registry.qualified(split=split, permitted_use="EVALUATION")
    prediction_by_id = {item["fixture_id"]: item for item in predictions}
    totals = {"tp": 0, "fp": 0, "fn": 0, "iou_sum": 0.0, "iou_count": 0, "keypoint_hits": 0, "keypoint_count": 0}
    status_counts: dict[str, int] = {}
    strata: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for fixture in fixtures:
        prediction = prediction_by_id.get(fixture["fixture_id"])
        if prediction is None:
            missing.append(fixture["fixture_id"])
            continue
        truth = fixture.get("truth", {})
        truth_zones = truth.get("zones", {})
        predicted_zones = prediction.get("zones", {})
        for zone_id in sorted(set(truth_zones) | set(predicted_zones)):
            expected = truth_zones.get(zone_id, {"present": False})
            observed = predicted_zones.get(zone_id, {"present": False, "status": "UNDECLARED"})
            expected_present = bool(expected.get("present"))
            observed_present = bool(observed.get("present"))
            if expected_present and observed_present:
                totals["tp"] += 1
            elif observed_present:
                totals["fp"] += 1
            elif expected_present:
                totals["fn"] += 1
            status = str(observed.get("status", "UNKNOWN"))
            status_counts[status] = status_counts.get(status, 0) + 1
            iou = _rect_iou(expected.get("rect"), observed.get("rect"))
            if iou is not None:
                totals["iou_sum"] += iou
                totals["iou_count"] += 1
            keypoint_hit = _keypoint_hit(
                expected.get("keypoint"), observed.get("keypoint"), keypoint_tolerance
            )
            if keypoint_hit is not None:
                totals["keypoint_count"] += 1
                totals["keypoint_hits"] += int(keypoint_hit)
            stratum_name = "/".join(
                (
                    str(truth.get("template_stratum", "UNKNOWN_TEMPLATE")),
                    str(expected.get("zone_type", zone_id)),
                )
            )
            bucket = strata.setdefault(stratum_name, {"count": 0, "tp": 0})
            bucket["count"] += 1
            bucket["tp"] += int(expected_present and observed_present)
    precision_denominator = totals["tp"] + totals["fp"]
    recall_denominator = totals["tp"] + totals["fn"]
    stratum_results = {
        name: {
            **bucket,
            "presence_recall": bucket["tp"] / bucket["count"] if bucket["count"] else None,
            "evidence_state": (
                "MEASURED" if bucket["count"] >= minimum_stratum_size else "EVIDENCE_REQUIRED"
            ),
        }
        for name, bucket in sorted(strata.items())
    }
    return {
        "schema_version": "zone-localization-scorecard-v1",
        "registry_id": registry.payload.get("registry_id"),
        "fixture_split": split,
        "presence_precision": (
            totals["tp"] / precision_denominator if precision_denominator else None
        ),
        "presence_recall": totals["tp"] / recall_denominator if recall_denominator else None,
        "mean_iou": totals["iou_sum"] / totals["iou_count"] if totals["iou_count"] else None,
        "keypoint_tolerance": keypoint_tolerance,
        "keypoint_accuracy": (
            totals["keypoint_hits"] / totals["keypoint_count"]
            if totals["keypoint_count"]
            else None
        ),
        "localization_status_counts": dict(sorted(status_counts.items())),
        "strata": stratum_results,
        "missing_predictions": sorted(missing),
        "claim_state": "EVIDENCE_REQUIRED" if missing or not fixtures else "MEASURED",
    }


def _rect_iou(expected: Any, observed: Any) -> float | None:
    if not (
        isinstance(expected, list)
        and isinstance(observed, list)
        and len(expected) == len(observed) == 4
    ):
        return None
    ex1, ey1, ex2, ey2 = map(float, expected)
    ox1, oy1, ox2, oy2 = map(float, observed)
    intersection = max(0.0, min(ex2, ox2) - max(ex1, ox1)) * max(
        0.0, min(ey2, oy2) - max(ey1, oy1)
    )
    union = max(0.0, ex2 - ex1) * max(0.0, ey2 - ey1) + max(
        0.0, ox2 - ox1
    ) * max(0.0, oy2 - oy1) - intersection
    return intersection / union if union else 0.0


def _keypoint_hit(expected: Any, observed: Any, tolerance: float) -> bool | None:
    if not (
        isinstance(expected, list)
        and isinstance(observed, list)
        and len(expected) == len(observed) == 2
    ):
        return None
    distance_squared = (float(expected[0]) - float(observed[0])) ** 2 + (
        float(expected[1]) - float(observed[1])
    ) ** 2
    return distance_squared <= tolerance**2


def score_typed_extraction(
    registry: GroundTruthRegistry,
    predictions: list[dict[str, Any]],
    *,
    split: str = "evaluation",
) -> dict[str, Any]:
    fixtures = registry.qualified(split=split, permitted_use="EVALUATION")
    prediction_by_id = {item["fixture_id"]: item for item in predictions}
    by_zone_type: dict[str, dict[str, int]] = {}
    missing: list[str] = []
    for fixture in fixtures:
        prediction = prediction_by_id.get(fixture["fixture_id"])
        if prediction is None:
            missing.append(fixture["fixture_id"])
            continue
        truth_zones = fixture.get("truth", {}).get("zones", {})
        observed_zones = prediction.get("zones", {})
        for zone_id, truth in truth_zones.items():
            zone_type = str(truth.get("zone_type", zone_id))
            bucket = by_zone_type.setdefault(
                zone_type,
                {"total": 0, "correct": 0, "unsupported": 0, "no_signal": 0, "failed": 0},
            )
            bucket["total"] += 1
            observed = observed_zones.get(zone_id, {"state": "UNSUPPORTED"})
            state = observed.get("state")
            if state == "SUCCEEDED":
                bucket["correct"] += int(observed.get("typed_value") == truth.get("typed_value"))
            elif state == "UNSUPPORTED":
                bucket["unsupported"] += 1
            elif state == "NO_SIGNAL":
                bucket["no_signal"] += 1
            else:
                bucket["failed"] += 1
    metrics = {}
    for zone_type, bucket in sorted(by_zone_type.items()):
        total = bucket["total"]
        metrics[zone_type] = {
            **bucket,
            "typed_accuracy": bucket["correct"] / total if total else None,
            "unsupported_rate": bucket["unsupported"] / total if total else None,
            "no_signal_rate": bucket["no_signal"] / total if total else None,
            "failure_rate": bucket["failed"] / total if total else None,
        }
    return {
        "schema_version": "typed-extraction-scorecard-v1",
        "registry_id": registry.payload.get("registry_id"),
        "fixture_split": split,
        "by_zone_type": metrics,
        "missing_predictions": sorted(missing),
        "claim_state": "EVIDENCE_REQUIRED" if missing or not fixtures else "MEASURED",
    }


def score_candidate_and_decision_safety(
    registry: GroundTruthRegistry,
    predictions: list[dict[str, Any]],
    *,
    split: str = "evaluation",
    top_k: int = 5,
) -> dict[str, Any]:
    fixtures = registry.qualified(split=split, permitted_use="EVALUATION")
    prediction_by_id = {item["fixture_id"]: item for item in predictions}
    counts = {
        "evaluated": 0,
        "candidate_hits": 0,
        "identity_correct": 0,
        "printing_total": 0,
        "printing_correct": 0,
        "unresolved": 0,
        "automatic_confirmations": 0,
        "false_automatic_confirmations": 0,
        "false_human_confirmations": 0,
    }
    missing: list[str] = []
    for fixture in fixtures:
        prediction = prediction_by_id.get(fixture["fixture_id"])
        if prediction is None:
            missing.append(fixture["fixture_id"])
            continue
        truth = fixture.get("truth", {})
        expected_identity = truth.get("canonical_reference_id")
        expected_printing = truth.get("printing_id")
        candidates = prediction.get("candidate_ids", [])[:top_k]
        state = prediction.get("decision_state")
        selected_identity = prediction.get("selected_reference_card_id")
        selected_printing = prediction.get("selected_printing_id")
        counts["evaluated"] += 1
        counts["candidate_hits"] += int(expected_identity in candidates)
        counts["identity_correct"] += int(selected_identity == expected_identity)
        if expected_printing is not None:
            counts["printing_total"] += 1
            counts["printing_correct"] += int(selected_printing == expected_printing)
        counts["unresolved"] += int(
            state
            in {
                "PROBABLE",
                "AMBIGUOUS",
                "INSUFFICIENT_EVIDENCE",
                "CONFLICTING_EVIDENCE",
                "NO_REFERENCE_MATCH",
            }
        )
        if state == "CONFIRMED_AUTOMATIC":
            counts["automatic_confirmations"] += 1
            counts["false_automatic_confirmations"] += int(
                selected_identity != expected_identity
                or (
                    expected_printing is not None
                    and selected_printing != expected_printing
                )
            )
        if state == "CONFIRMED_HUMAN":
            counts["false_human_confirmations"] += int(
                selected_identity != expected_identity
                or (
                    expected_printing is not None
                    and selected_printing != expected_printing
                )
            )
    evaluated = counts["evaluated"]
    automatic = counts["automatic_confirmations"]
    return {
        "schema_version": "candidate-decision-safety-scorecard-v1",
        "registry_id": registry.payload.get("registry_id"),
        "fixture_split": split,
        "top_k": top_k,
        **counts,
        "candidate_top_k_recall": counts["candidate_hits"] / evaluated if evaluated else None,
        "exact_identity_rate": counts["identity_correct"] / evaluated if evaluated else None,
        "exact_printing_rate": (
            counts["printing_correct"] / counts["printing_total"]
            if counts["printing_total"]
            else None
        ),
        "unresolved_rate": counts["unresolved"] / evaluated if evaluated else None,
        "false_automatic_confirmation_rate": (
            counts["false_automatic_confirmations"] / automatic if automatic else 0.0
        ),
        "automatic_confirmation_policy": "PROHIBITED",
        "automatic_confirmation_policy_test": (
            "PASS" if automatic == 0 else "FAIL"
        ),
        "threshold_adoption": "NOT_ADOPTED",
        "missing_predictions": sorted(missing),
        "claim_state": "EVIDENCE_REQUIRED" if missing or not fixtures else "MEASURED",
    }
