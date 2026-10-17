from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

import cv2

from .candidates import retrieve_candidates, select_discriminator
from .decision import decide
from .ocr import OCRProvider, classify_script, parse_collector_number, parse_hp
from .store import ReferenceStore
from .template_registry import TemplateRegistry, crop_zone
from .util import ensure_write_path, sha256_file, unique_path, utc_now, write_json_new
from .vision import (
    detect_nine_pocket_cards,
    load_image,
    normalized_to_source_rect,
    predict_templates,
    visual_features,
)


PIPELINE_VERSION = "pre-alpha-vertical-slice-v1"


def analyze_page(
    image_path: Path,
    database_path: Path,
    template_root: Path,
    output_parent: Path,
    ocr_provider: OCRProvider,
) -> dict[str, Any]:
    image_path = image_path.resolve(strict=True)
    database_path = database_path.resolve(strict=True)
    source_hash = sha256_file(image_path)
    output_parent = ensure_write_path(output_parent)
    output_parent.mkdir(parents=True, exist_ok=True)
    run_directory = unique_path(output_parent / f"run-{source_hash[:12]}")
    run_directory.mkdir(parents=False, exist_ok=False)
    crops_directory = run_directory / "crops"
    zones_directory = run_directory / "zones"
    evidence_directory = run_directory / "evidence"
    for directory in (crops_directory, zones_directory, evidence_directory):
        directory.mkdir()

    source_image = load_image(image_path)
    detected_cards, page_geometry = detect_nine_pocket_cards(source_image)
    registry = TemplateRegistry(template_root)
    template_findings = registry.validate()
    if template_findings:
        raise ValueError("invalid template registry: " + "; ".join(template_findings))
    store = ReferenceStore(database_path)
    card_packages: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []
    try:
        for detected in detected_cards:
            crop_path = crops_directory / f"pocket-{detected.pocket_index:02d}.png"
            if not cv2.imwrite(str(crop_path), detected.normalized):
                raise RuntimeError(f"failed to write normalized crop: {crop_path}")
            features = visual_features(detected.normalized)

            # A candidate historical title-band read precedes template selection;
            # the raw observation remains distinct from the later hypothesis.
            historical = registry.resolve("pokemon.ja.vs-owner.v1")
            title_crop, title_rect = crop_zone(detected.normalized, historical["zones"]["title"])
            title_ocr = ocr_provider.read(title_crop)
            script = classify_script(title_ocr)
            template_predictions = predict_templates(features, script["japanese_character_fraction"])
            selected_template = registry.resolve(template_predictions[0]["template_id"])

            observations: dict[str, Any] = {}
            for zone_id in ("title", "hp"):
                zone = selected_template["zones"][zone_id]
                zone_crop, rect = crop_zone(detected.normalized, zone)
                zone_path = zones_directory / f"pocket-{detected.pocket_index:02d}-{zone_id}.png"
                if not cv2.imwrite(str(zone_path), zone_crop):
                    raise RuntimeError(f"failed to write zone crop: {zone_path}")
                ocr = title_ocr if zone_id == "title" else ocr_provider.read(
                    zone_crop, allowlist="HP0123456789"
                )
                typed_value = (
                    parse_hp(ocr) or parse_hp(title_ocr)
                    if zone_id == "hp"
                    else ocr.get("normalized_text")
                )
                observations[zone_id] = _zone_observation(
                    zone_id,
                    zone,
                    rect,
                    detected.source_polygon,
                    zone_path,
                    ocr,
                    typed_value,
                )

            initial_candidates = retrieve_candidates(
                store, observations, template_predictions[0], limit=25
            )
            discriminator = select_discriminator(initial_candidates, observations)
            if discriminator == "collector_number":
                zone = selected_template["zones"]["collector_number"]
                zone_crop, rect = crop_zone(detected.normalized, zone)
                zone_path = zones_directory / (
                    f"pocket-{detected.pocket_index:02d}-collector-number.png"
                )
                if not cv2.imwrite(str(zone_path), zone_crop):
                    raise RuntimeError(f"failed to write zone crop: {zone_path}")
                ocr = ocr_provider.read(zone_crop, allowlist="0123456789/／")
                observations["collector_number"] = _zone_observation(
                    "collector_number",
                    zone,
                    rect,
                    detected.source_polygon,
                    zone_path,
                    ocr,
                    parse_collector_number(ocr),
                )

            candidates = retrieve_candidates(store, observations, template_predictions[0], limit=25)
            image_evidence = {
                "state": "reference_image_unavailable",
                "reason": "No locally permitted TCGdex image is registered for VS1 candidates.",
                "comparison_performed": False,
            }
            decision = decide(candidates, detected.quality)
            package = {
                "schema_version": "card-evidence-v1",
                "pipeline_version": PIPELINE_VERSION,
                "capture": {
                    "source_path": str(image_path),
                    "source_sha256": source_hash,
                    "source_dimensions": page_geometry["source_dimensions"],
                },
                "card_face_observation": {
                    "pocket_index": detected.pocket_index,
                    "source_polygon": detected.source_polygon,
                    "normalized_crop": str(crop_path.relative_to(run_directory)),
                    "orientation": "portrait",
                    "geometry_method": detected.geometry_method,
                    "quality": detected.quality,
                    "visual_features": features,
                    "script_observation": script,
                    "template_predictions": template_predictions,
                    "selected_template_id": selected_template["template_id"],
                    "selected_template_lineage": selected_template.get("resolved_lineage", []),
                },
                "zone_observations": observations,
                "candidate_assessments": candidates,
                "discriminator_plan": {
                    "selected_zone": discriminator,
                    "strategy": "greatest available identifier value among unresolved candidates",
                },
                "reference_image_evidence": image_evidence,
                "identification_decision": decision,
                "truth_separation": {
                    "reference_truth": "candidate_assessments originate in the pinned local corpus",
                    "observation_truth": "zone_observations preserve raw OCR and typed parsing",
                    "decision_truth": "identification_decision is policy output and not reference fact",
                },
                "generated_at": utc_now(),
            }
            evidence_path = write_json_new(
                evidence_directory / f"pocket-{detected.pocket_index:02d}.json", package
            )
            package["evidence_path"] = str(evidence_path.relative_to(run_directory))
            card_packages.append(package)
            selected = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate["reference_card_id"] == decision["selected_reference_card_id"]
                ),
                None,
            )
            inventory_rows.append(
                {
                    "collection_id": "sample-collection",
                    "binder_id": "sample-binder",
                    "page_id": source_hash[:12],
                    "pocket_index": detected.pocket_index,
                    "canonical_reference_id": decision["selected_reference_card_id"],
                    "display_name": selected.get("display_name") if selected else None,
                    "set_id": selected.get("set_id") if selected else None,
                    "collector_number": selected.get("local_id") if selected else None,
                    "identification_state": decision["state"],
                    "confidence": decision["confidence"],
                    "review_status": "required" if decision["human_review_required"] else "not_required",
                    "capture_sha256": source_hash,
                }
            )
    finally:
        store.close()

    summary = {
        "schema_version": "page-run-v1",
        "run_id": run_directory.name,
        "pipeline_version": PIPELINE_VERSION,
        "source": {
            "path": str(image_path),
            "sha256": source_hash,
            "immutable_input": True,
        },
        "page_geometry": page_geometry,
        "pocket_order": [package["card_face_observation"]["pocket_index"] for package in card_packages],
        "decision_counts": _counts(
            [package["identification_decision"]["state"] for package in card_packages]
        ),
        "cards": [
            {
                "pocket_index": package["card_face_observation"]["pocket_index"],
                "decision": package["identification_decision"],
                "evidence_path": package["evidence_path"],
                "top_candidates": package["candidate_assessments"][:5],
            }
            for package in card_packages
        ],
        "nonclaims": [
            "This single fixture does not establish general accuracy.",
            "No TCGdex VS1 reference imagery was available for independent image confirmation.",
            "PROBABLE and AMBIGUOUS are not confirmed identifications.",
            "Printing variants remain unresolved without printing-specific evidence.",
        ],
        "generated_at": utc_now(),
    }
    summary_path = write_json_new(run_directory / "page-summary.json", summary)
    _write_inventory(run_directory, inventory_rows)
    summary["run_directory"] = str(run_directory)
    summary["summary_path"] = str(summary_path)
    return summary


def _zone_observation(
    zone_id: str,
    zone: dict[str, Any],
    normalized_rect: list[int],
    source_polygon: list[list[int]],
    artifact_path: Path,
    ocr: dict[str, Any],
    typed_value: Any,
) -> dict[str, Any]:
    return {
        "semantic_zone": zone_id,
        "normalized_template_rect": zone["rect"],
        "normalized_pixel_rect": normalized_rect,
        "source_polygon": normalized_to_source_rect(normalized_rect, source_polygon),
        "artifact_path": str(artifact_path),
        "extractor_configuration": zone.get("extractor"),
        "ocr": ocr,
        "typed_value": typed_value,
    }


def _counts(values: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


def _write_inventory(run_directory: Path, rows: list[dict[str, Any]]) -> None:
    jsonl_path = run_directory / "inventory.jsonl"
    with jsonl_path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    csv_path = run_directory / "inventory.csv"
    with csv_path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    sqlite_path = run_directory / "inventory.sqlite3"
    connection = sqlite3.connect(sqlite_path)
    columns = ", ".join(f'"{field}" TEXT' for field in rows[0])
    connection.execute(f"CREATE TABLE inventory ({columns})")
    placeholders = ", ".join("?" for _ in rows[0])
    connection.executemany(
        f"INSERT INTO inventory VALUES ({placeholders})",
        [[None if value is None else str(value) for value in row.values()] for row in rows],
    )
    connection.commit()
    connection.close()
