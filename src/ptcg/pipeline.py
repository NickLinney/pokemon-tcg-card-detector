from __future__ import annotations

import csv
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Callable

import cv2

from .candidates import retrieve_candidates, select_discriminator
from .decision import decide
from .evidence import ContentAddressedArtifactStore
from .localization import (
    attach_extraction,
    initialize_zone_observations,
    localize_zone_proposals,
)
from .ocr import OCRProvider, classify_script, parse_collector_number, parse_hp
from .run_control import RunLedger, RunManifest
from .run_catalog import seal_artifact_index
from .store import ReferenceStore
from .symbols import SymbolProvider, UnsupportedSymbolProvider
from .template_registry import TemplateRegistry, crop_zone
from .util import ensure_write_path, sha256_file, unique_path, utc_now, write_json_new
from .vision import (
    classify_template_hierarchy,
    detect_cards,
    load_image,
    visual_features,
)
from .workflow import default_sample_context, location_id, validate_collection_context


PIPELINE_VERSION = "pre-alpha-evidence-architecture-v7"
SCHEMA_VERSIONS = {
    "card_evidence": "card-evidence-v2",
    "page_run": "page-run-v2",
    "run_manifest": "run-manifest-v1",
    "run_transition": "run-transition-v1",
    "template_classification": "template-classification-v1",
    "zone_observation": "zone-observation-v2",
}


def analyze_page(
    image_path: Path,
    database_path: Path,
    template_root: Path,
    output_parent: Path,
    ocr_provider: OCRProvider,
    *,
    idempotency_key: str | None = None,
    context: dict[str, Any] | None = None,
    cancel_check: Callable[[], None] | None = None,
    symbol_provider: SymbolProvider | None = None,
) -> dict[str, Any]:
    image_path = image_path.resolve(strict=True)
    database_path = database_path.resolve(strict=True)
    template_root = template_root.resolve(strict=True)
    source_hash = sha256_file(image_path)
    database_hash = sha256_file(database_path)
    context = validate_collection_context(context) if context is not None else default_sample_context()
    cancel_check = cancel_check or (lambda: None)
    symbol_provider = symbol_provider or UnsupportedSymbolProvider()
    cancel_check()

    registry = TemplateRegistry(template_root)
    template_findings = registry.validate()
    if template_findings:
        raise ValueError("invalid template registry: " + "; ".join(template_findings))

    configuration = {
        "template_root": str(template_root),
        "ocr_provider": ocr_provider.provider_id,
        "analysis_profile": "local-offline-pre-alpha",
        "network_acquisition": False,
        "automatic_confirmation": False,
        "zone_crop_policy": "all-declared-applicable-priors",
        "collection_context": context,
    }
    manifest = RunManifest.build(
        source_sha256=source_hash,
        corpus_sha256=database_hash,
        template_registry_sha256=registry.digest(),
        pipeline_version=PIPELINE_VERSION,
        ocr_provider=ocr_provider.provider_id,
        schema_versions=SCHEMA_VERSIONS,
        configuration=configuration,
        idempotency_key=idempotency_key,
    )

    output_parent = ensure_write_path(output_parent)
    output_parent.mkdir(parents=True, exist_ok=True)
    base_name = f"run-{source_hash[:12]}-{manifest.digest[:8]}"
    requested_directory = output_parent / base_name
    if idempotency_key is not None and requested_directory.exists():
        return _read_idempotent_result(requested_directory, manifest)
    run_directory = (
        requested_directory
        if idempotency_key is not None
        else unique_path(requested_directory)
    )
    run_directory.mkdir(parents=False, exist_ok=False)
    evidence_directory = run_directory / "evidence"
    transitions_directory = run_directory / "transitions"
    evidence_directory.mkdir()
    artifacts = ContentAddressedArtifactStore(run_directory / "artifacts")
    source_artifact = artifacts.put_file(
        image_path,
        media_type=_image_media_type(image_path),
        role="immutable-source-capture",
    )
    manifest.payload["source_artifact"] = source_artifact
    write_json_new(run_directory / "run-manifest.json", manifest.payload)
    ledger = RunLedger(
        transitions_directory,
        run_id=run_directory.name,
        manifest_id=manifest.payload["manifest_id"],
    )
    ledger.transition(
        "ADMITTED",
        reason="Manifest bindings and template registry verified.",
        evidence_refs=[source_artifact["artifact_id"]],
    )

    store: ReferenceStore | None = None
    try:
        source_image = load_image(image_path)
        cancel_check()
        ledger.transition(
            "INGESTED",
            reason="Source decoded within configured bounds; original bytes retained immutably.",
            evidence_refs=[source_artifact["artifact_id"]],
        )
        detected_cards, page_geometry = detect_cards(source_image)
        cancel_check()
        ledger.transition(
            "GEOMETRY_COMPLETE",
            reason="Supported geometry baseline produced reversible source polygons.",
        )

        card_contexts: list[dict[str, Any]] = []
        neutral_template = registry.resolve("card.base.v1")
        for detected in detected_cards:
            cancel_check()
            normalized_ref = artifacts.put_bytes(
                _encode_png(detected.normalized),
                media_type="image/png",
                role=f"normalized-card:pocket-{detected.pocket_index:02d}",
            )
            features = visual_features(detected.normalized)

            # Family-neutral input prevents a family-specific crop from proving
            # the same template hypothesis that selected it.
            neutral_title_crop, _ = crop_zone(
                detected.normalized, neutral_template["zones"]["title"]
            )
            neutral_title_ref = artifacts.put_bytes(
                _encode_png(neutral_title_crop),
                media_type="image/png",
                role=f"classification-input:title:pocket-{detected.pocket_index:02d}",
            )
            preliminary_title_ocr = ocr_provider.read(neutral_title_crop)
            script = classify_script(preliminary_title_ocr)
            classification = classify_template_hierarchy(features, script, registry)
            classification["input_artifacts"] = [neutral_title_ref]
            selected_template = registry.resolve(classification["selected_for_localization"])
            observations = initialize_zone_observations(
                selected_template, detected.source_polygon, detected.quality
            )
            localize_zone_proposals(
                detected.normalized, observations, detected.source_polygon
            )

            for zone_id, observation in observations.items():
                zone_crop, _ = crop_zone(detected.normalized, selected_template["zones"][zone_id])
                crop_ref = artifacts.put_bytes(
                    _encode_png(zone_crop),
                    media_type="image/png",
                    role=f"zone-prior:{zone_id}:pocket-{detected.pocket_index:02d}",
                )
                attach_extraction(
                    observation,
                    artifact_ref=crop_ref,
                    ocr=None,
                    typed_value=None,
                    attempted=False,
                )

            _extract_declared_zones(
                detected.normalized,
                selected_template,
                observations,
                ocr_provider,
                symbol_provider,
            )
            cancel_check()
            card_contexts.append(
                {
                    "detected": detected,
                    "normalized_ref": normalized_ref,
                    "features": features,
                    "script": script,
                    "classification": classification,
                    "selected_template": selected_template,
                    "observations": observations,
                }
            )

        ledger.transition(
            "TEMPLATE_HYPOTHESES_READY",
            reason="Hierarchical uncalibrated hypotheses and UNKNOWN_FAMILY escape recorded for every card.",
        )
        ledger.transition(
            "INITIAL_OBSERVATIONS_READY",
            reason="Every declared zone has an explicit observation/presence state and immutable prior crop.",
        )

        store = ReferenceStore(database_path)
        for context in card_contexts:
            prediction = context["classification"]["template_hypotheses"][0]
            observations = context["observations"]
            initial_candidates = retrieve_candidates(store, observations, prediction, limit=25)
            discriminator = select_discriminator(initial_candidates, observations)
            if (
                discriminator == "collector_number"
                and "collector_number" in observations
                and not observations["collector_number"]["extractor_attempts"]
            ):
                _extract_ocr_zone(
                    context["detected"].normalized,
                    context["selected_template"],
                    observations,
                    "collector_number",
                    ocr_provider,
                    allowlist="0123456789/／",
                    parser=parse_collector_number,
                )
            context["initial_candidates"] = initial_candidates
            context["discriminator"] = discriminator
            context["candidates"] = retrieve_candidates(
                store, observations, prediction, limit=25
            )

        ledger.transition(
            "CANDIDATES_READY",
            reason="Recall-oriented local candidate sets and bounded discriminator choices recorded.",
        )
        ledger.transition(
            "EVIDENCE_FUSED",
            reason="Current vertical-slice comparison signals compiled; dependency-aware fusion remains future work.",
        )

        card_packages: list[dict[str, Any]] = []
        inventory_rows: list[dict[str, Any]] = []
        for context in card_contexts:
            detected = context["detected"]
            classification = context["classification"]
            selected_template = context["selected_template"]
            observations = context["observations"]
            candidates = context["candidates"]
            decision = decide(candidates, detected.quality)
            image_evidence = {
                "state": "reference_image_unavailable",
                "reason": "No locally permitted reference image is registered for these candidates.",
                "comparison_performed": False,
            }
            package = {
                "schema_version": SCHEMA_VERSIONS["card_evidence"],
                "pipeline_version": PIPELINE_VERSION,
                "run_manifest_id": manifest.payload["manifest_id"],
                "capture": {
                    "source_artifact": source_artifact,
                    "source_sha256": source_hash,
                    "source_dimensions": page_geometry["source_dimensions"],
                },
                "card_face_observation": {
                    "pocket_index": detected.pocket_index,
                    "source_polygon": detected.source_polygon,
                    "normalized_crop_artifact": context["normalized_ref"],
                    "orientation": "portrait",
                    "geometry_method": detected.geometry_method,
                    "quality": detected.quality,
                    "visual_features": context["features"],
                    "script_observation": context["script"],
                    "template_classification": classification,
                    "template_predictions": classification["template_hypotheses"],
                    "localization_template_id": selected_template["template_id"],
                    "localization_template_is_fact": False,
                    "selected_template_lineage": selected_template.get("resolved_lineage", []),
                },
                "zone_observations": observations,
                "zone_coverage": {
                    "declared": len(selected_template.get("zones", {})),
                    "observed_records": len(observations),
                    "missing_records": sorted(
                        set(selected_template.get("zones", {})) - set(observations)
                    ),
                    "independently_localized": sum(
                        1 for item in observations.values() if item.get("localized") is not None
                    ),
                    "extraction_states": _counts(
                        [item["extraction_state"] for item in observations.values()]
                    ),
                },
                "candidate_assessments": candidates,
                "discriminator_plan": {
                    "selected_zone": context["discriminator"],
                    "strategy": "greatest available identifier value among unresolved candidates",
                    "bounded_rounds": 1,
                    "termination_reason": "single-round Pre-Alpha discriminator budget exhausted",
                },
                "reference_image_evidence": image_evidence,
                "identification_decision": decision,
                "truth_separation": {
                    "reference_truth": "candidate assessments originate in the pinned local corpus",
                    "observation_truth": "zone records retain priors, raw extraction, and localization limits",
                    "decision_truth": "identification decision is uncalibrated policy output, not reference fact",
                },
                "generated_at": utc_now(),
            }
            payload_ref = artifacts.put_json(
                package, role=f"card-evidence-payload:pocket-{detected.pocket_index:02d}"
            )
            package["evidence_payload_artifact"] = payload_ref
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
                    "collection_id": context["collection_id"],
                    "binder_id": context["binder_id"],
                    "page_id": context["page_id"],
                    "pocket_index": detected.pocket_index,
                    "location_id": location_id(context, detected.pocket_index),
                    "canonical_reference_id": decision["selected_reference_card_id"],
                    "display_name": selected.get("display_name") if selected else None,
                    "set_id": selected.get("set_id") if selected else None,
                    "collector_number": selected.get("local_id") if selected else None,
                    "identification_state": decision["state"],
                    "confidence": decision["confidence"],
                    "review_status": "required",
                    "projection_state": "PROPOSAL_NOT_EFFECTIVE",
                    "capture_sha256": source_hash,
                }
            )

        ledger.transition(
            "DECIDED",
            reason="Uncalibrated abstaining policy produced qualified decisions; automatic confirmation is disabled.",
            evidence_refs=[
                item["evidence_payload_artifact"]["artifact_id"] for item in card_packages
            ],
        )
        review_required = any(
            package["identification_decision"]["human_review_required"]
            for package in card_packages
        )
        if review_required:
            ledger.transition(
                "REVIEW_REQUIRED",
                reason="One or more qualified decisions require an accountable human review disposition.",
            )
        else:
            ledger.transition(
                "INVENTORY_PROJECTED",
                reason="All decisions were eligible for inventory projection under the bound policy.",
            )

        summary = {
            "schema_version": SCHEMA_VERSIONS["page_run"],
            "run_id": run_directory.name,
            "run_state": ledger.state,
            "run_manifest_id": manifest.payload["manifest_id"],
            "pipeline_version": PIPELINE_VERSION,
            "collection_context": context,
            "source": {
                "artifact": source_artifact,
                "sha256": source_hash,
                "immutable_input": True,
            },
            "page_geometry": page_geometry,
            "template_registry": {
                "sha256": registry.digest(),
                "coverage": registry.coverage(),
            },
            "pocket_order": [
                package["card_face_observation"]["pocket_index"]
                for package in card_packages
            ],
            "decision_counts": _counts(
                [package["identification_decision"]["state"] for package in card_packages]
            ),
            "zone_observation_totals": {
                "declared_and_recorded": sum(
                    package["zone_coverage"]["observed_records"] for package in card_packages
                ),
                "independently_localized": sum(
                    package["zone_coverage"]["independently_localized"]
                    for package in card_packages
                ),
                "extraction_states": _merge_counts(
                    [package["zone_coverage"]["extraction_states"] for package in card_packages]
                ),
            },
            "cards": [
                {
                    "pocket_index": package["card_face_observation"]["pocket_index"],
                    "decision": package["identification_decision"],
                    "evidence_path": package["evidence_path"],
                    "evidence_artifact": package["evidence_payload_artifact"],
                    "template_classification": package["card_face_observation"][
                        "template_classification"
                    ],
                    "zone_coverage": package["zone_coverage"],
                    "top_candidates": package["candidate_assessments"][:5],
                }
                for package in card_packages
            ],
            "nonclaims": [
                "This single fixture does not establish general accuracy.",
                "Template scores are uncalibrated ranking signals, not probabilities or facts.",
                "All declared zones have records and prior crops; image-supported proposals remain provisional and uncalibrated.",
                "Reference imagery is unavailable unless separately rights-approved and registered.",
                "PROBABLE and AMBIGUOUS are not confirmed identifications.",
                "Printing variants remain unresolved without printing-specific evidence.",
            ],
            "generated_at": utc_now(),
        }
        summary_path = write_json_new(run_directory / "page-summary.json", summary)
        cancel_check()
        _write_inventory(run_directory, inventory_rows)
        indexed_artifacts = [
            {
                **source_artifact,
                "safe_filename": f"source{image_path.suffix.lower()}",
                "downloadable": True,
            }
        ]
        for path, media_type, role in (
            (summary_path, "application/json", "page-summary"),
            (run_directory / "inventory.csv", "text/csv", "inventory-csv"),
            (run_directory / "inventory.jsonl", "application/x-ndjson", "inventory-jsonl"),
            (run_directory / "inventory.sqlite3", "application/vnd.sqlite3", "inventory-sqlite"),
        ):
            indexed_artifacts.append(
                {
                    **artifacts.put_file(path, media_type=media_type, role=role),
                    "safe_filename": path.name,
                    "downloadable": True,
                }
            )
        for package in card_packages:
            pocket = package["card_face_observation"]["pocket_index"]
            indexed_artifacts.append(
                {
                    **package["evidence_payload_artifact"],
                    "safe_filename": f"pocket-{pocket:02d}-evidence.json",
                    "downloadable": True,
                }
            )
        seal_artifact_index(run_directory, indexed_artifacts)
        summary["run_directory"] = str(run_directory)
        summary["summary_path"] = str(summary_path)
        return summary
    except Exception as exc:
        ledger.fail(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if store is not None:
            store.close()


def _extract_ocr_zone(
    image,
    template: dict[str, Any],
    observations: dict[str, dict[str, Any]],
    zone_id: str,
    provider: OCRProvider,
    *,
    allowlist: str | None = None,
    parser=None,
) -> None:
    if zone_id not in observations:
        return
    crop, _ = crop_zone(image, template["zones"][zone_id])
    ocr = provider.read(crop, allowlist=allowlist)
    typed_value = parser(ocr) if parser else ocr.get("normalized_text")
    observation = observations[zone_id]
    attach_extraction(
        observation,
        artifact_ref=observation["prior_crop_artifact"],
        ocr=ocr,
        typed_value=typed_value,
        attempted=True,
    )


def _extract_declared_zones(
    image,
    template: dict[str, Any],
    observations: dict[str, dict[str, Any]],
    provider: OCRProvider,
    symbol_provider: SymbolProvider,
) -> None:
    for zone_id, zone in template.get("zones", {}).items():
        extractor_provider = zone.get("extractor", {}).get("provider")
        data_type = zone.get("data_type")
        if extractor_provider in {"ocr", "ocr-symbol", "symbol-ocr"}:
            allowlist = None
            parser = None
            if zone_id == "hp":
                allowlist = "HP0123456789"
                parser = parse_hp
            elif zone_id == "collector_number":
                allowlist = "0123456789/／"
                parser = parse_collector_number
            elif data_type == "integer":
                allowlist = "0123456789x×+-"
                parser = _parse_first_integer
            _extract_ocr_zone(
                image,
                template,
                observations,
                zone_id,
                provider,
                allowlist=allowlist,
                parser=parser,
            )
        elif extractor_provider == "image-feature":
            crop, _ = crop_zone(image, zone)
            observation = observations[zone_id]
            attach_extraction(
                observation,
                artifact_ref=observation["prior_crop_artifact"],
                ocr=None,
                typed_value={
                    "descriptor_state": "LOCAL_UNCOMPARED",
                    "visual_features": visual_features(crop),
                },
                attempted=True,
                provider_id="opencv:visual-features-v1",
            )
        elif extractor_provider == "symbol":
            crop, _ = crop_zone(image, zone)
            observation = observations[zone_id]
            result = symbol_provider.extract(
                crop,
                zone_id=zone_id,
                template_id=template["template_id"],
            )
            if result["state"] == "UNSUPPORTED":
                observation["extraction_state"] = "UNSUPPORTED"
                observation["extractor_attempts"].append(
                    {
                        "provider": result["provider"],
                        "raw_preserved": True,
                        "result": "UNSUPPORTED",
                        "artifact_id": observation["prior_crop_artifact"]["artifact_id"],
                        "warning": result["uncertainty"],
                    }
                )
            else:
                attach_extraction(
                    observation,
                    artifact_ref=observation["prior_crop_artifact"],
                    ocr=None,
                    typed_value=result["typed_value"],
                    attempted=True,
                    provider_id=result["provider"],
                )
                observation["symbol_result"] = result


def _parse_first_integer(ocr: dict[str, Any]) -> int | None:
    match = re.search(r"\d{1,4}", ocr.get("raw_text", ""))
    return int(match.group(0)) if match else None


def _encode_png(image) -> bytes:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("failed to encode PNG artifact")
    return encoded.tobytes()


def _read_idempotent_result(run_directory: Path, manifest: RunManifest) -> dict[str, Any]:
    from .audit import verify_run

    manifest_path = run_directory / "run-manifest.json"
    summary_path = run_directory / "page-summary.json"
    if not manifest_path.is_file() or not summary_path.is_file():
        raise ValueError(
            f"idempotency collision with incomplete run; inspect or resume: {run_directory}"
        )
    existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if existing_manifest.get("manifest_id") != manifest.payload["manifest_id"]:
        raise ValueError("idempotency key collision across different run manifests")
    audit = verify_run(run_directory)
    if audit["status"] != "PASS":
        raise ValueError(
            f"idempotent run failed integrity verification: {audit['findings']}"
        )
    result = json.loads(summary_path.read_text(encoding="utf-8"))
    result["run_directory"] = str(run_directory)
    result["summary_path"] = str(summary_path)
    result["idempotent_replay"] = True
    result["idempotent_replay_integrity"] = "PASS"
    return result


def _image_media_type(path: Path) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")


def _counts(values: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return dict(sorted(result.items()))


def _merge_counts(counts: list[dict[str, int]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for count in counts:
        for key, value in count.items():
            result[key] = result.get(key, 0) + value
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
