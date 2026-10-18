from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from .template_registry import normalized_rect
from .vision import normalized_to_source_rect


PRESENCE_STATES = (
    "PRESENT",
    "ABSENT",
    "NOT_APPLICABLE",
    "NOT_LOCALIZED",
    "OCCLUDED",
    "UNREADABLE",
)


def initialize_zone_observations(
    template: dict[str, Any],
    source_polygon: list[list[int]],
    quality: dict[str, float],
) -> dict[str, dict[str, Any]]:
    """Create one honest observation shell for every resolved template zone.

    Static template rectangles are retained as priors. They are deliberately
    not mislabeled as detector-produced localized polygons.
    """
    observations: dict[str, dict[str, Any]] = {}
    for zone_id, zone in sorted(template.get("zones", {}).items()):
        rect = normalized_rect(zone)
        prior_pixel_rect = _normalized_to_pixel_rect(rect)
        applicable = _applicable(zone, template)
        observations[zone_id] = {
            "schema_version": "zone-observation-v2",
            "semantic_zone": zone_id,
            "semantic_family": zone.get("semantic_family", "unclassified"),
            "template_id": template["template_id"],
            "applicable": applicable,
            "presence_state": "NOT_LOCALIZED" if applicable else "NOT_APPLICABLE",
            "prior": {
                "normalized_rect": rect,
                "normalized_pixel_rect": prior_pixel_rect,
                "source_polygon": normalized_to_source_rect(prior_pixel_rect, source_polygon),
                "basis": "versioned template registry definition",
            },
            "localized": None,
            "localization": {
                "method": "template-prior-only",
                "locator_contract": zone.get("locator"),
                "confidence": 0.0,
                "independent_pixel_evidence": False,
                "reason": (
                    "No independent anchor/proposal localizer is implemented in this increment."
                    if applicable
                    else "Zone applicability predicate evaluated false."
                ),
                "alternatives": [],
            },
            "quality": {
                "glare_fraction": quality.get("glare_fraction"),
                "blur_indicator": quality.get("laplacian_variance"),
                "effective_width_px": prior_pixel_rect[2] - prior_pixel_rect[0],
                "effective_height_px": prior_pixel_rect[3] - prior_pixel_rect[1],
            },
            "cardinality": zone.get("cardinality", "one"),
            "data_type": zone.get("data_type"),
            "extractor_configuration": zone.get("extractor"),
            "extraction_state": "NOT_ATTEMPTED" if applicable else "NOT_APPLICABLE",
            "extractor_attempts": [],
            "typed_value": None,
        }
    return observations


def attach_extraction(
    observation: dict[str, Any],
    *,
    artifact_ref: dict[str, Any],
    ocr: dict[str, Any] | None,
    typed_value: Any,
    attempted: bool,
    provider_id: str | None = None,
) -> None:
    observation["prior_crop_artifact"] = artifact_ref
    if not attempted:
        observation["extraction_state"] = "UNSUPPORTED"
        return
    observation["ocr"] = ocr
    observation["typed_value"] = typed_value
    has_signal = bool((ocr or {}).get("raw_text")) or typed_value is not None
    observation["extraction_state"] = "SUCCEEDED" if has_signal else "NO_SIGNAL"
    observation["extractor_attempts"].append(
        {
            "provider": provider_id or (ocr or {}).get("provider"),
            "raw_preserved": True,
            "result": observation["extraction_state"],
            "artifact_id": artifact_ref["artifact_id"],
            "warning": (
                "Extraction used a template-prior crop; no independent localized polygon exists."
                if observation.get("localized") is None
                else "Extraction used the template-prior crop; the provisional pixel proposal was not used to recrop."
            ),
        }
    )


def localize_zone_proposals(
    image: np.ndarray,
    observations: dict[str, dict[str, Any]],
    source_polygon: list[list[int]],
) -> None:
    """Refine priors with bounded image-edge proposals.

    The proposal is independent pixel evidence but its semantic assignment is
    still template-conditioned and therefore explicitly provisional.
    """
    height, width = image.shape[:2]
    for observation in observations.values():
        if not observation["applicable"]:
            continue
        x0, y0, x1, y1 = observation["prior"]["normalized_pixel_rect"]
        x0, x1 = max(0, x0), min(width, x1)
        y0, y1 = max(0, y0), min(height, y1)
        crop = image[y0:y1, x0:x1]
        if crop.size == 0:
            observation["localization"]["reason"] = "Template prior produced an empty search window."
            continue
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        contrast = float(np.percentile(gray, 98) - np.percentile(gray, 2))
        median = float(np.median(gray))
        low = int(max(0, 0.66 * median))
        high = int(min(255, max(low + 1, 1.33 * median)))
        edges = cv2.Canny(gray, low, high)
        edge_fraction = float((edges > 0).mean())
        ys, xs = np.where(edges > 0)
        if contrast < 8.0 or edge_fraction < 0.003 or len(xs) < 8:
            observation["localization"].update(
                {
                    "method": "template-conditioned-edge-proposal-v1",
                    "confidence": 0.0,
                    "independent_pixel_evidence": True,
                    "reason": "No bounded edge proposal met the minimum contrast/support checks.",
                    "diagnostics": {
                        "contrast_span": round(contrast, 4),
                        "edge_fraction": round(edge_fraction, 6),
                    },
                }
            )
            continue

        local_x0, local_x1 = (int(np.quantile(xs, q)) for q in (0.01, 0.99))
        local_y0, local_y1 = (int(np.quantile(ys, q)) for q in (0.01, 0.99))
        localized_rect = [
            max(x0, x0 + local_x0 - 2),
            max(y0, y0 + local_y0 - 2),
            min(x1, x0 + local_x1 + 3),
            min(y1, y0 + local_y1 + 3),
        ]
        proposal_width = localized_rect[2] - localized_rect[0]
        proposal_height = localized_rect[3] - localized_rect[1]
        if proposal_width < 3 or proposal_height < 3:
            observation["localization"]["reason"] = "Pixel proposal collapsed below minimum size."
            continue
        signal = min(0.85, 0.2 + min(contrast / 255.0, 0.4) + min(edge_fraction, 0.25))
        observation["localized"] = {
            "normalized_pixel_rect": localized_rect,
            "normalized_rect": [
                round(localized_rect[0] / width, 8),
                round(localized_rect[1] / height, 8),
                round(proposal_width / width, 8),
                round(proposal_height / height, 8),
            ],
            "source_polygon": normalized_to_source_rect(
                localized_rect, source_polygon, normalized_shape=(height, width)
            ),
            "semantic_assignment_state": "PROVISIONAL_TEMPLATE_CONDITIONED",
        }
        observation["presence_state"] = "PRESENT"
        observation["localization"].update(
            {
                "method": "template-conditioned-edge-proposal-v1",
                "confidence": round(signal, 6),
                "confidence_semantics": "uncalibrated-ranking-signal",
                "independent_pixel_evidence": True,
                "reason": "Edge-supported proposal found inside the bounded template-prior search window.",
                "diagnostics": {
                    "contrast_span": round(contrast, 4),
                    "edge_fraction": round(edge_fraction, 6),
                },
            }
        )


def _applicable(zone: dict[str, Any], template: dict[str, Any]) -> bool:
    applicability = zone.get("applicability")
    if not applicability or applicability == "always":
        return True
    if isinstance(applicability, dict):
        return all(template.get(key) == value for key, value in applicability.items())
    return True


def _normalized_to_pixel_rect(rect: list[float]) -> list[int]:
    x, y, width, height = rect
    card_width, card_height = 630, 880
    return [
        max(0, round(x * card_width)),
        max(0, round(y * card_height)),
        min(card_width, round((x + width) * card_width)),
        min(card_height, round((y + height) * card_height)),
    ]
