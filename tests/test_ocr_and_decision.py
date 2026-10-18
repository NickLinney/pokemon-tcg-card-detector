from ptcg.decision import decide
from ptcg.ocr import parse_collector_number, parse_hp


def test_numeric_ocr_parsers_keep_raw_separate():
    assert parse_hp({"raw_text": "HP6O"}) == 60
    assert parse_collector_number({"raw_text": "016 / 141"}) == {
        "local_id": "016",
        "set_count": "141",
    }


def test_tied_candidates_remain_ambiguous():
    candidate = {
        "reference_card_id": "a",
        "fused_score": 0.9,
        "evidence": [{"family": "structured", "strength": 1.0}],
        "contradictions": [],
    }
    result = decide([candidate, candidate | {"reference_card_id": "b"}], {"glare_fraction": 0.0, "laplacian_variance": 100})
    assert result["state"] == "AMBIGUOUS"
    assert result["selected_reference_card_id"] is None


def test_conflict_prevents_confirmation():
    candidate = {
        "reference_card_id": "a",
        "fused_score": 0.99,
        "evidence": [
            {"family": "identifier", "strength": 1.0},
            {"family": "image", "strength": 1.0},
        ],
        "contradictions": ["collector number differs"],
    }
    assert decide([candidate], {"glare_fraction": 0.0, "laplacian_variance": 100})["state"] == "CONFLICTING_EVIDENCE"


def test_uncalibrated_policy_never_confirms_automatically():
    candidate = {
        "reference_card_id": "a",
        "fused_score": 0.99,
        "evidence": [
            {"family": "identifier", "strength": 1.0},
            {"family": "image", "strength": 1.0},
        ],
        "contradictions": [],
    }
    result = decide(
        [candidate], {"glare_fraction": 0.0, "laplacian_variance": 100}
    )
    assert result["state"] == "PROBABLE"
    assert result["calibration_state"] == "EVIDENCE_REQUIRED"
    assert result["prediction_is_confirmation"] is False
