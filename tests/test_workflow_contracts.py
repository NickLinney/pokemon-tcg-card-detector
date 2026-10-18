import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).parents[1]
NOW = "2026-10-18T12:00:00Z"
SHA = "a" * 64


def validate(name: str, value: dict) -> None:
    schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(value)


def test_workflow_contract_examples_validate():
    context = {
        "schema_version": "collection-context-v1",
        "collection_id": "collection:one",
        "binder_id": "binder.one",
        "page_id": "page-1",
        "source_captured_at": NOW,
    }
    validate("collection-context.schema.json", context)
    validate(
        "analysis-job.schema.json",
        {
            "schema_version": "analysis-job-v1",
            "job_id": "job-" + "1" * 32,
            "state": "ADMITTED",
            "context": context,
            "source_sha256": SHA,
            "idempotency_key_sha256": "b" * 64,
            "run_id": None,
            "error": None,
            "created_at": NOW,
            "updated_at": NOW,
        },
    )
    validate(
        "artifact-descriptor.schema.json",
        {"schema_version": "artifact-descriptor-v1", "artifact_id": "sha256:" + SHA, "run_id": "run-1", "sha256": SHA, "bytes": 3, "media_type": "text/csv", "role": "inventory-csv", "safe_filename": "inventory.csv", "downloadable": True},
    )
    review_id = "review-" + SHA
    validate(
        "review-case.schema.json",
        {"schema_version": "review-case-v1", "review_id": review_id, "run_id": "run-1", "location_id": "collection:one/binder.one/page-1/pocket-01", "state": "REQUIRED", "evidence_version": "sha256:" + SHA, "candidate_refs": [], "artifact_refs": ["sha256:" + SHA]},
    )
    disposition = {
        "schema_version": "review-disposition-v1",
        "disposition_id": "sha256:" + SHA,
        "review_id": review_id,
        "actor_id": "local:reviewer",
        "authority_scope": "collection:one",
        "action": "LEAVE_UNRESOLVED",
        "reason": "Evidence remains insufficient.",
        "identity_assertion": None,
        "printing_assertion": None,
        "field_correction": None,
        "evidence_version": "sha256:" + SHA,
        "expected_prior_assertion": None,
        "occurred_at": NOW,
    }
    validate("review-disposition.schema.json", disposition)
    validate(
        "superseding-assertion.schema.json",
        {"schema_version": "superseding-assertion-v1", "assertion_id": "sha256:" + SHA, "location_id": "location-1", "source_disposition_id": "sha256:" + SHA, "supersedes": None, "effective_state": {"state": "UNRESOLVED"}, "created_at": NOW},
    )
    validate(
        "effective-inventory-projection.schema.json",
        {"schema_version": "effective-inventory-projection-v1", "projection_id": "sha256:" + SHA, "projection_version": "effective-inventory-projector-v1", "collection_id": "collection:one", "generated_at": NOW, "items": []},
    )


def test_context_rejects_path_and_empty_identifiers():
    with pytest.raises(ValidationError):
        validate(
            "collection-context.schema.json",
            {"schema_version": "collection-context-v1", "collection_id": "../escape", "binder_id": "", "page_id": "page-1"},
        )


def test_openapi_tracks_canonical_version_and_required_surface():
    document = yaml.safe_load((ROOT / "docs" / "api" / "openapi.yaml").read_text())
    assert document["openapi"] == "3.1.0"
    assert document["info"]["version"] == "0.2.0-pre-alpha.2"
    required = {
        "/v1/analysis-jobs",
        "/v1/analysis-jobs/{job_id}",
        "/v1/analysis-jobs/{job_id}:cancel",
        "/v1/runs/{run_id}",
        "/v1/runs/{run_id}/artifacts",
        "/v1/runs/{run_id}/artifacts/{artifact_id}",
        "/v1/reviews",
        "/v1/reviews/{review_id}",
        "/v1/reviews/{review_id}/dispositions",
        "/v1/inventories/{collection_id}",
    }
    assert required <= set(document["paths"])
