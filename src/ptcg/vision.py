from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

if TYPE_CHECKING:
    from .template_registry import TemplateRegistry


CARD_WIDTH = 630
CARD_HEIGHT = 880


@dataclass(frozen=True)
class DetectedCard:
    pocket_index: int
    source_polygon: list[list[int]]
    normalized: np.ndarray
    quality: dict[str, float]
    geometry_method: str


def detect_cards(image: np.ndarray) -> tuple[list[DetectedCard], dict[str, Any]]:
    """Detect a supported page layout, falling back to a bounded single card.

    The nine-pocket detector remains the only multi-card implementation. The
    fallback is explicit and does not claim arbitrary-page support.
    """
    try:
        return detect_nine_pocket_cards(image)
    except ValueError as nine_pocket_error:
        height, width = image.shape[:2]
        aspect_ratio = width / height
        if not 0.58 <= aspect_ratio <= 0.86:
            raise ValueError(
                "unsupported capture geometry: neither nine-pocket evidence nor "
                "a portrait single-card aspect ratio was detected"
            ) from nine_pocket_error
        polygon = [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]
        normalized = cv2.resize(image, (CARD_WIDTH, CARD_HEIGHT), interpolation=cv2.INTER_AREA)
        card = DetectedCard(
            pocket_index=1,
            source_polygon=polygon,
            normalized=normalized,
            quality=quality_metrics(normalized),
            geometry_method="single-card-full-frame-v1",
        )
        return [card], {
            "method": "single-card-full-frame-v1",
            "page_card_envelope": polygon,
            "grid_shape": [1, 1],
            "detected_observation_count": 1,
            "source_dimensions": {"width": width, "height": height},
            "qualification": (
                "Full-frame portrait fallback; card corners were not independently detected."
            ),
        }


def load_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"unsupported or unreadable image: {path}")
    if image.size > 100_000_000:
        raise ValueError("decoded image exceeds the bounded 100-megapixel limit")
    return image


def detect_nine_pocket_cards(image: np.ndarray) -> tuple[list[DetectedCard], dict[str, Any]]:
    """Infer a 3x3 grid from repeated high-saturation yellow card borders.

    The detector does not assume every pocket contains a card. Cells whose
    border signal is materially weaker than the page median are retained as
    low-quality observations rather than silently discarded.
    """
    height, width = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    yellow = (
        (hsv[:, :, 0] >= 7)
        & (hsv[:, :, 0] <= 48)
        & (hsv[:, :, 1] >= 55)
        & (hsv[:, :, 2] >= 55)
    )
    ys, xs = np.where(yellow)
    if len(xs) < width * height * 0.02:
        raise ValueError("insufficient repeated border evidence for nine-pocket inference")

    # The 1% lower quantile rejects small yellow/holographic binder artifacts
    # while retaining the three repeated card columns.
    xmin, xmax = (int(np.quantile(xs, q)) for q in (0.01, 0.995))
    ymin, ymax = (int(np.quantile(ys, q)) for q in (0.003, 0.997))
    x_step = (xmax - xmin) / 3
    y_step = (ymax - ymin) / 3
    x_projection = yellow.mean(axis=0)
    y_projection = yellow.mean(axis=1)

    lefts: list[int] = []
    for col in range(3):
        start = round(xmin + col * x_step)
        stop = round(start + x_step * 0.38)
        peak = start + int(np.argmax(x_projection[start:stop]))
        lefts.append(max(0, round(peak - x_step * 0.045)))
    rights = [
        max(lefts[index] + 10, round(lefts[index + 1] - x_step * 0.05))
        for index in range(2)
    ] + [min(width - 1, round(xmax + x_step * 0.01))]

    bottom_peaks: list[int] = []
    for row in range(3):
        band_start = round(ymin + row * y_step + y_step * 0.57)
        band_stop = min(
            height,
            round(ymin + (row + (0.90 if row < 2 else 1.0)) * y_step),
        )
        peak = band_start + int(np.argmax(y_projection[band_start:band_stop]))
        bottom_peaks.append(peak)
    tops = [max(0, ymin)] + [
        min(height - 2, round(bottom_peaks[index] + y_step * 0.095))
        for index in range(2)
    ]
    bottoms = [
        min(height - 1, round(peak + y_step * 0.05)) for peak in bottom_peaks
    ]

    cards: list[DetectedCard] = []
    cell_signals: list[float] = []
    for row in range(3):
        for col in range(3):
            x0, x1 = lefts[col], rights[col]
            y0, y1 = tops[row], bottoms[row]
            if x1 <= x0 or y1 <= y0:
                raise ValueError("invalid inferred pocket geometry")
            polygon = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
            source = np.float32(polygon)
            destination = np.float32(
                [[0, 0], [CARD_WIDTH - 1, 0], [CARD_WIDTH - 1, CARD_HEIGHT - 1], [0, CARD_HEIGHT - 1]]
            )
            matrix = cv2.getPerspectiveTransform(source, destination)
            normalized = cv2.warpPerspective(image, matrix, (CARD_WIDTH, CARD_HEIGHT))
            signal = float(yellow[y0:y1, x0:x1].mean())
            cell_signals.append(signal)
            cards.append(
                DetectedCard(
                    pocket_index=row * 3 + col + 1,
                    source_polygon=polygon,
                    normalized=normalized,
                    quality=quality_metrics(normalized) | {"border_signal_fraction": round(signal, 6)},
                    geometry_method="yellow-border-projection-grid-v1",
                )
            )
    page = {
        "method": "yellow-border-projection-grid-v1",
        "page_card_envelope": [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]],
        "grid_shape": [3, 3],
        "detected_observation_count": len(cards),
        "border_signal_median": round(float(np.median(cell_signals)), 6),
        "source_dimensions": {"width": width, "height": height},
    }
    return cards, page


def quality_metrics(image: np.ndarray) -> dict[str, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    glare = float((gray >= 245).mean())
    underexposed = float((gray <= 18).mean())
    return {
        "laplacian_variance": round(blur_variance, 4),
        "glare_fraction": round(glare, 6),
        "underexposed_fraction": round(underexposed, 6),
        "effective_width_px": float(image.shape[1]),
        "effective_height_px": float(image.shape[0]),
    }


def visual_features(image: np.ndarray) -> dict[str, float]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    rim = np.zeros(hsv.shape[:2], dtype=bool)
    margin_x = max(1, image.shape[1] // 18)
    margin_y = max(1, image.shape[0] // 18)
    rim[:margin_y, :] = True
    rim[-margin_y:, :] = True
    rim[:, :margin_x] = True
    rim[:, -margin_x:] = True
    yellow = (
        (hsv[:, :, 0] >= 7)
        & (hsv[:, :, 0] <= 48)
        & (hsv[:, :, 1] >= 55)
        & (hsv[:, :, 2] >= 55)
    )
    green = (
        (hsv[:, :, 0] >= 35)
        & (hsv[:, :, 0] <= 95)
        & (hsv[:, :, 1] >= 45)
    )
    return {
        "yellow_border_fraction": round(float(yellow[rim].mean()), 6),
        "green_face_fraction": round(float(green.mean()), 6),
        "aspect_ratio": round(image.shape[1] / image.shape[0], 6),
    }


def classify_template_hierarchy(
    features: dict[str, float],
    script_observation: dict[str, Any],
    registry: "TemplateRegistry",
    *,
    top_k: int = 5,
) -> dict[str, Any]:
    """Produce provisional coarse-to-fine hypotheses without forced fitting.

    This is a deterministic rules baseline, not a calibrated classifier. Scores
    are ranking signals and are explicitly prohibited from being represented as
    probabilities until benchmark calibration exists.
    """
    yellow = float(features.get("yellow_border_fraction", 0.0))
    japanese_fraction = float(script_observation.get("japanese_character_fraction", 0.0))
    japanese_supported = japanese_fraction >= 0.2

    template_hypotheses: list[dict[str, Any]] = []
    for template_id in registry.candidate_ids():
        template = registry.resolve(template_id)
        score = 0.08
        reasons: list[str] = []
        support_depth = "category"

        category = template.get("category", "Unknown")
        if category == "Pokemon":
            score += 0.12
            reasons.append("Pokémon category retained as a weak baseline hypothesis")
        elif category in {"Trainer", "Energy"}:
            score += 0.06
            reasons.append(f"{category} category retained because no category detector is available")

        if template.get("language") == "ja":
            if japanese_supported:
                score += 0.30
                reasons.append("family-neutral title crop contains Japanese-script evidence")
                support_depth = "script_language"
            else:
                reasons.append("Japanese-language requirement is not yet supported by OCR evidence")

        era = template.get("era")
        border = template.get("predicates", {}).get("border")
        if border == "yellow" or era == "historical" or isinstance(era, int):
            score += min(0.28, yellow * 0.32)
            reasons.append("yellow-border geometry supports a historical layout family")
            support_depth = "era_layout"
        elif era == "modern":
            score += max(0.0, (1.0 - yellow) * 0.22)
            reasons.append("reduced yellow-border evidence supports the modern alternative")
            support_depth = "era_layout"

        if template.get("series_hint"):
            score -= 0.06
            reasons.append(
                "set/mechanic-specific family is penalized until an independent marker is observed"
            )
        template_hypotheses.append(
            {
                "template_id": template_id,
                "score": round(max(0.0, min(score, 0.95)), 6),
                "score_semantics": "uncalibrated-ranking-signal",
                "support_depth": support_depth,
                "hierarchy": {
                    "category": category,
                    "script": script_observation.get("script", "Unknown"),
                    "language": template.get("language", "Unknown"),
                    "region": template.get("region", "Unknown"),
                    "era_layout": era or "Unknown",
                    "mechanic_form": template.get("mechanic", "Unknown"),
                    "printing_overlay": "Unknown",
                },
                "reasons": reasons,
                "series_hint": template.get("series_hint"),
            }
        )

    template_hypotheses.sort(key=lambda item: (-item["score"], item["template_id"]))
    template_hypotheses = template_hypotheses[:top_k]
    top_score = template_hypotheses[0]["score"] if template_hypotheses else 0.0
    runner_up = template_hypotheses[1]["score"] if len(template_hypotheses) > 1 else 0.0
    margin = top_score - runner_up
    forced_fit_risk = top_score < 0.55 or margin < 0.08
    unknown_score = round(max(0.05, 1.0 - top_score + max(0.0, 0.08 - margin)), 6)

    hierarchy_levels = [
        _level("product_scope", [("PHYSICAL_POKEMON_TCG", 0.8, "card-like geometry detected"), ("UNKNOWN", 0.2, "scope classifier not independently benchmarked")]),
        _level("face_state", [("FRONT", 0.7, "front-like border/layout signal"), ("UNKNOWN", 0.3, "back/empty/occluded detector not implemented")]),
        _level("orientation", [("PORTRAIT", 0.98, "normalized crop aspect ratio"), ("UNKNOWN", 0.02, "rotation classifier not implemented")]),
        _level("category", [("POKEMON", 0.45, "weak registry prior"), ("UNKNOWN", 0.4, "category detector not implemented"), ("TRAINER_OR_ENERGY", 0.15, "retained alternative")]),
        _level(
            "script",
            [
                ("JAPANESE", round(japanese_fraction, 6), "OCR Unicode-range evidence"),
                ("UNKNOWN", round(1.0 - japanese_fraction, 6), "insufficient or non-Japanese OCR signal"),
            ],
        ),
        _level(
            "language",
            [
                ("JAPANESE", round(japanese_fraction, 6), "script-derived language evidence"),
                ("UNKNOWN", round(1.0 - japanese_fraction, 6), "language is not inferred without script support"),
            ],
        ),
        _level("region", [("UNKNOWN", 1.0, "region-specific evidence is not implemented")]),
        _level(
            "era_layout",
            [
                ("HISTORICAL", round(min(0.9, 0.2 + yellow * 0.7), 6), "yellow-border layout evidence"),
                ("MODERN", round(max(0.05, 0.65 - yellow * 0.55), 6), "contrasting layout alternative"),
                ("UNKNOWN", 0.35, "era classifier is not calibrated"),
            ],
        ),
        _level(
            "template_family",
            [
                (
                    item["template_id"],
                    item["score"],
                    "; ".join(item["reasons"]) or "registry candidate",
                )
                for item in template_hypotheses
            ]
            + [("UNKNOWN_FAMILY", unknown_score, "explicit forced-fit escape")],
        ),
        _level("mechanic_form", [("UNKNOWN", 1.0, "independent mechanic detector not implemented")]),
        _level("set_card_exception", [("UNKNOWN", 1.0, "exception evidence is not implemented")]),
        _level("printing_overlay", [("UNKNOWN", 1.0, "printing evidence not available")]),
    ]
    return {
        "schema_version": "template-classification-v1",
        "classifier_version": "deterministic-hierarchy-baseline-v1",
        "calibration_state": "EVIDENCE_REQUIRED",
        "hierarchy_levels": hierarchy_levels,
        "template_hypotheses": template_hypotheses,
        "unknown_family": {
            "template_id": "UNKNOWN_FAMILY",
            "score": unknown_score,
            "state": "OUT_OF_DISTRIBUTION_POSSIBLE" if forced_fit_risk else "KNOWN_FAMILY_PLAUSIBLE",
            "reasons": [
                "No calibrated learned classifier or representative taxonomy benchmark is available.",
                "Fine-grained mechanic and printing levels intentionally remain unknown.",
            ],
        },
        "ensemble_disagreement": {
            "state": "UNMEASURED",
            "reason": "Only one deterministic baseline method is implemented.",
        },
        "selected_for_localization": (
            template_hypotheses[0]["template_id"] if template_hypotheses else "card.base.v1"
        ),
        "selected_is_fact": False,
        "nonclaims": [
            "Scores are not calibrated probabilities.",
            "A localization template is a working prior, not a classified template fact.",
        ],
    }


def predict_templates(features: dict[str, float], japanese_fraction: float) -> list[dict[str, Any]]:
    """Backward-compatible two-family baseline retained for external callers.

    New application code uses :func:`classify_template_hierarchy` with a
    registry. This compatibility function does not claim hierarchy coverage.
    """
    yellow = features["yellow_border_fraction"]
    historical_score = min(0.86, 0.30 + yellow * 0.55 + japanese_fraction * 0.25)
    modern_score = max(0.05, 0.42 - yellow * 0.30)
    return sorted(
        [
            {
                "template_id": "pokemon.ja.historical.v1",
                "score": round(historical_score, 4),
                "score_semantics": "uncalibrated-ranking-signal",
                "reasons": ["historical border and script baseline"],
                "series_hint": None,
            },
            {
                "template_id": "pokemon.modern-standard.v1",
                "score": round(modern_score, 4),
                "score_semantics": "uncalibrated-ranking-signal",
                "reasons": ["modern family retained as alternative"],
                "series_hint": None,
            },
        ],
        key=lambda item: item["score"],
        reverse=True,
    )


def _level(name: str, hypotheses: list[tuple[str, float, str]]) -> dict[str, Any]:
    return {
        "level": name,
        "hypotheses": [
            {"value": value, "score": score, "reason": reason}
            for value, score, reason in hypotheses
        ],
    }


def normalized_to_source_rect(
    normalized_rect: list[int], source_polygon: list[list[int]], normalized_shape=(CARD_HEIGHT, CARD_WIDTH)
) -> list[list[int]]:
    """Map an axis-aligned normalized crop back to the source quadrilateral."""
    x0, y0, x1, y1 = normalized_rect
    h, w = normalized_shape
    source = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    target = np.float32(source_polygon)
    matrix = cv2.getPerspectiveTransform(source, target)
    points = np.float32([[[x0, y0], [x1, y0], [x1, y1], [x0, y1]]])
    mapped = cv2.perspectiveTransform(points, matrix)[0]
    return [[round(float(x)), round(float(y))] for x, y in mapped]
