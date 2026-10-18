from __future__ import annotations

from typing import Any


POLICY_VERSION = "explicit-rules-v2-uncalibrated"
CALIBRATION_STATE = "EVIDENCE_REQUIRED"


def decide(candidates: list[dict[str, Any]], quality: dict[str, float]) -> dict[str, Any]:
    if not candidates:
        return _decision("NO_REFERENCE_MATCH", None, 0.0, ["no local candidates"])
    first = candidates[0]
    second_score = candidates[1]["fused_score"] if len(candidates) > 1 else 0.0
    margin = first["fused_score"] - second_score
    families = {
        evidence["family"]
        for evidence in first["evidence"]
        if evidence.get("strength", 0) >= 0.7
    }
    contradictions = first.get("contradictions", [])
    low_quality = quality.get("glare_fraction", 0) > 0.32 or quality.get("laplacian_variance", 0) < 35
    if contradictions:
        state = "CONFLICTING_EVIDENCE"
    elif len(families) >= 2 and first["fused_score"] >= 0.88 and margin >= 0.15 and not low_quality:
        # The target architecture prohibits automatic confirmation until the
        # policy is calibrated against an accepted held-out benchmark.
        state = "PROBABLE"
    elif first["fused_score"] >= 0.62 and margin >= 0.1:
        state = "PROBABLE"
    elif margin < 0.1 and len(candidates) > 1:
        state = "AMBIGUOUS"
    else:
        state = "INSUFFICIENT_EVIDENCE"
    selected = first["reference_card_id"] if state in {"CONFIRMED_AUTOMATIC", "PROBABLE"} else None
    reasons = [
        f"top score={first['fused_score']:.4f}",
        f"runner-up margin={margin:.4f}",
        f"strong evidence families={sorted(families)}",
    ]
    if low_quality:
        reasons.append("image quality gate not satisfied")
    if state == "PROBABLE" and len(families) >= 2:
        reasons.append("automatic confirmation disabled: calibration evidence required")
    reasons.extend(contradictions)
    return _decision(state, selected, first["fused_score"], reasons, margin)


def _decision(
    state: str,
    selected_reference_card_id: str | None,
    confidence: float,
    reasons: list[str],
    margin: float = 0.0,
) -> dict[str, Any]:
    return {
        "state": state,
        "selected_reference_card_id": selected_reference_card_id,
        "selected_variant": None,
        "confidence": round(float(confidence), 6),
        "runner_up_margin": round(float(margin), 6),
        "policy_version": POLICY_VERSION,
        "calibration_state": CALIBRATION_STATE,
        "reasons": reasons,
        "human_review_required": state != "CONFIRMED_AUTOMATIC",
        "prediction_is_confirmation": state.startswith("CONFIRMED_"),
    }
