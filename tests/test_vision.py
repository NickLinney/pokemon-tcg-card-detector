from pathlib import Path

import pytest

from ptcg.template_registry import TemplateRegistry
import numpy as np

from ptcg.vision import (
    classify_template_hierarchy,
    detect_cards,
    detect_nine_pocket_cards,
    load_image,
)


SAMPLE = Path(__file__).resolve().parents[2] / "binder-ingest-images/samples/000-first-sample.jpeg"


@pytest.mark.skipif(not SAMPLE.exists(), reason="commissioned sample fixture is not present")
def test_sample_segments_nine_cards_in_row_major_order():
    cards, page = detect_nine_pocket_cards(load_image(SAMPLE))
    assert [card.pocket_index for card in cards] == list(range(1, 10))
    assert all(card.normalized.shape[:2] == (880, 630) for card in cards)
    assert page["detected_observation_count"] == 9
    for card in cards:
        xs = [point[0] for point in card.source_polygon]
        ys = [point[1] for point in card.source_polygon]
        assert min(xs) >= 0 and max(xs) <= page["source_dimensions"]["width"]
        assert min(ys) >= 0 and max(ys) <= page["source_dimensions"]["height"]


def test_template_classifier_emits_hierarchy_top_k_and_unknown_escape():
    registry = TemplateRegistry(Path(__file__).parents[1] / "templates")
    result = classify_template_hierarchy(
        {"yellow_border_fraction": 0.8, "green_face_fraction": 0.2, "aspect_ratio": 0.716},
        {"script": "Japanese", "japanese_character_fraction": 0.8},
        registry,
    )
    assert result["calibration_state"] == "EVIDENCE_REQUIRED"
    assert result["unknown_family"]["template_id"] == "UNKNOWN_FAMILY"
    assert result["selected_is_fact"] is False
    assert {item["level"] for item in result["hierarchy_levels"]} >= {
        "product_scope",
        "face_state",
        "orientation",
        "category",
        "script",
        "language",
        "region",
        "era_layout",
        "template_family",
        "mechanic_form",
        "set_card_exception",
        "printing_overlay",
    }
    assert len(result["template_hypotheses"]) >= 2


def test_portrait_single_card_fallback_is_explicitly_qualified():
    image = np.full((880, 630, 3), 128, dtype=np.uint8)
    cards, geometry = detect_cards(image)
    assert len(cards) == 1
    assert cards[0].normalized.shape[:2] == (880, 630)
    assert geometry["method"] == "single-card-full-frame-v1"
    assert "not independently detected" in geometry["qualification"]
