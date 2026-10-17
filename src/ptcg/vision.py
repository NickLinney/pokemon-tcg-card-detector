from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


CARD_WIDTH = 630
CARD_HEIGHT = 880


@dataclass(frozen=True)
class DetectedCard:
    pocket_index: int
    source_polygon: list[list[int]]
    normalized: np.ndarray
    quality: dict[str, float]
    geometry_method: str


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


def predict_templates(features: dict[str, float], japanese_fraction: float) -> list[dict[str, Any]]:
    yellow = features["yellow_border_fraction"]
    historical_score = min(0.92, 0.38 + yellow * 0.65 + japanese_fraction * 0.25)
    modern_score = max(0.05, 0.48 - yellow * 0.35)
    predictions = [
        {
            "template_id": "pokemon.ja.vs-owner.v1",
            "score": round(historical_score, 4),
            "reasons": ["yellow historical border", "owner-associated VS geometry", "Japanese script evidence"],
            "series_hint": "VS",
        },
        {
            "template_id": "pokemon.modern-standard.v1",
            "score": round(modern_score, 4),
            "reasons": ["contrasting modern family retained as alternative"],
            "series_hint": None,
        },
    ]
    return sorted(predictions, key=lambda item: item["score"], reverse=True)


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
