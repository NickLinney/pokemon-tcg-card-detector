from pathlib import Path

import pytest

from ptcg.vision import detect_nine_pocket_cards, load_image


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
