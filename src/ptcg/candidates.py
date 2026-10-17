from __future__ import annotations

from typing import Any

from rapidfuzz.fuzz import ratio

from .store import ReferenceStore
from .util import normalize_text


def retrieve_candidates(
    store: ReferenceStore,
    observations: dict[str, Any],
    template_prediction: dict[str, Any],
    limit: int = 25,
) -> list[dict[str, Any]]:
    collector = observations.get("collector_number", {}).get("typed_value") or {}
    hp = observations.get("hp", {}).get("typed_value")
    query_hp = hp if isinstance(hp, int) else None
    pool = store.candidates(
        series_id=template_prediction.get("series_hint"),
        category="Pokemon",
        hp=query_hp,
        limit=1000,
    )
    if not pool and query_hp is not None:
        pool = store.candidates(
            series_id=template_prediction.get("series_hint"), category="Pokemon", limit=1000
        )
    title = observations.get("title", {}).get("ocr", {}).get("normalized_text")
    scored = []
    for card in pool:
        evidence: list[dict[str, Any]] = []
        contradictions: list[str] = []
        weighted = 0.0
        possible = 0.0
        if title:
            expected_names = [value for value in card["normalized_names"].values() if value]
            title_score = max((ratio(title, value) / 100 for value in expected_names), default=0.0)
            weighted += title_score * 0.36
            possible += 0.36
            evidence.append({"family": "text", "field": "name", "strength": round(title_score, 4)})
        if query_hp is not None:
            hp_match = card["hp"] == query_hp
            weighted += (1.0 if hp_match else 0.0) * 0.22
            possible += 0.22
            evidence.append({"family": "structured", "field": "hp", "strength": 1.0 if hp_match else 0.0})
            if not hp_match:
                contradictions.append("observed HP differs from reference HP")
        if collector.get("local_id"):
            observed = collector["local_id"].lstrip("0") or "0"
            expected = card["local_id"].lstrip("0") or "0"
            number_match = observed == expected
            weighted += (1.0 if number_match else 0.0) * 0.62
            possible += 0.62
            evidence.append(
                {"family": "identifier", "field": "collector_number", "strength": 1.0 if number_match else 0.0}
            )
            if not number_match:
                contradictions.append("observed collector number differs")
        template_strength = 1.0 if card["series_id"] == template_prediction.get("series_hint") else 0.25
        weighted += template_strength * 0.18
        possible += 0.18
        evidence.append({"family": "structural", "field": "template_series", "strength": template_strength})
        score = weighted / possible if possible else 0.0
        scored.append(
            {
                "reference_card_id": card["canonical_reference_id"],
                "source_card_id": card["source_card_id"],
                "display_name": card["names"].get("ja") or next(iter(card["names"].values()), None),
                "set_id": card["set_id"],
                "local_id": card["local_id"],
                "hp": card["hp"],
                "types": card["types"],
                "score_before_image": round(score, 6),
                "fused_score": round(score, 6),
                "evidence": evidence,
                "contradictions": contradictions,
                "missing_discriminators": _missing_discriminators(title, query_hp, collector),
            }
        )
    scored.sort(key=lambda item: (-item["fused_score"], item["reference_card_id"]))
    return scored[:limit]


def select_discriminator(candidates: list[dict[str, Any]], observations: dict[str, Any]) -> str | None:
    if len(candidates) <= 1:
        return None
    if not observations.get("collector_number", {}).get("typed_value"):
        return "collector_number"
    if not observations.get("title", {}).get("ocr", {}).get("normalized_text"):
        return "title"
    return "illustrator"


def _missing_discriminators(title, hp, collector) -> list[str]:
    missing = []
    if not collector:
        missing.append("collector_number")
    if not title:
        missing.append("title")
    if hp is None:
        missing.append("hp")
    missing.extend(["reference_image", "printing_variant"])
    return missing
