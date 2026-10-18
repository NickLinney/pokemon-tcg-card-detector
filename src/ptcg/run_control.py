from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .util import canonical_json_sha256, ensure_write_path, utc_now


RUN_MANIFEST_SCHEMA_VERSION = "run-manifest-v1"
RUN_TRANSITION_SCHEMA_VERSION = "run-transition-v1"


class IllegalRunTransition(ValueError):
    pass


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "REQUESTED": {"ADMITTED", "FAILED_QUALIFIED"},
    "ADMITTED": {"INGESTED", "FAILED_QUALIFIED"},
    "INGESTED": {"GEOMETRY_COMPLETE", "FAILED_QUALIFIED"},
    "GEOMETRY_COMPLETE": {"TEMPLATE_HYPOTHESES_READY", "FAILED_QUALIFIED"},
    "TEMPLATE_HYPOTHESES_READY": {"INITIAL_OBSERVATIONS_READY", "FAILED_QUALIFIED"},
    "INITIAL_OBSERVATIONS_READY": {"CANDIDATES_READY", "FAILED_QUALIFIED"},
    "CANDIDATES_READY": {"EVIDENCE_FUSED", "FAILED_QUALIFIED"},
    "EVIDENCE_FUSED": {"DECIDED", "FAILED_QUALIFIED"},
    "DECIDED": {"REVIEW_REQUIRED", "INVENTORY_PROJECTED", "FAILED_QUALIFIED"},
    "REVIEW_REQUIRED": {"REVIEWED", "FAILED_QUALIFIED"},
    "REVIEWED": {"INVENTORY_PROJECTED", "FAILED_QUALIFIED"},
    "INVENTORY_PROJECTED": set(),
    "FAILED_QUALIFIED": set(),
}


@dataclass(frozen=True)
class RunManifest:
    payload: dict[str, Any]

    @classmethod
    def build(
        cls,
        *,
        source_sha256: str,
        corpus_sha256: str,
        template_registry_sha256: str,
        pipeline_version: str,
        ocr_provider: str,
        schema_versions: dict[str, str],
        configuration: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> "RunManifest":
        configuration_digest = canonical_json_sha256(configuration)
        bindings = {
            "source_sha256": source_sha256,
            "corpus_sha256": corpus_sha256,
            "template_registry_sha256": template_registry_sha256,
            "pipeline_version": pipeline_version,
            "ocr_provider": ocr_provider,
            "schema_versions": dict(sorted(schema_versions.items())),
            "configuration_sha256": configuration_digest,
            "idempotency_key_sha256": (
                canonical_json_sha256({"idempotency_key": idempotency_key})
                if idempotency_key is not None
                else None
            ),
        }
        manifest_id = canonical_json_sha256(bindings)
        return cls(
            {
                "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
                "manifest_id": f"sha256:{manifest_id}",
                "bindings": bindings,
                "configuration": configuration,
                "created_at": utc_now(),
                "lifecycle_state": "SEALED_FOR_EXECUTION",
                "nonclaims": [
                    "A sealed run manifest is not production approval.",
                    "Version binding does not establish model accuracy or taxonomy acceptance.",
                ],
            }
        )

    @property
    def digest(self) -> str:
        return self.payload["manifest_id"].removeprefix("sha256:")


class RunLedger:
    """Append-only transition records with an explicitly checked state graph."""

    def __init__(self, root: Path, *, run_id: str, manifest_id: str):
        self.root = ensure_write_path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.manifest_id = manifest_id
        self.state = "REQUESTED"
        self.sequence = 0
        self._append_transition(None, "REQUESTED", "run request materialized", [])

    def transition(
        self,
        target: str,
        *,
        reason: str,
        evidence_refs: list[str] | None = None,
    ) -> dict[str, Any]:
        if target not in ALLOWED_TRANSITIONS:
            raise IllegalRunTransition(f"unknown run state: {target}")
        if target not in ALLOWED_TRANSITIONS[self.state]:
            raise IllegalRunTransition(f"illegal run transition: {self.state} -> {target}")
        source = self.state
        record = self._append_transition(source, target, reason, evidence_refs or [])
        self.state = target
        return record

    def fail(self, reason: str, *, evidence_refs: list[str] | None = None) -> dict[str, Any] | None:
        if self.state in {"FAILED_QUALIFIED", "INVENTORY_PROJECTED"}:
            return None
        if "FAILED_QUALIFIED" not in ALLOWED_TRANSITIONS[self.state]:
            return None
        return self.transition(
            "FAILED_QUALIFIED", reason=reason, evidence_refs=evidence_refs or []
        )

    def _append_transition(
        self,
        source: str | None,
        target: str,
        reason: str,
        evidence_refs: list[str],
    ) -> dict[str, Any]:
        self.sequence += 1
        body = {
            "schema_version": RUN_TRANSITION_SCHEMA_VERSION,
            "run_id": self.run_id,
            "manifest_id": self.manifest_id,
            "sequence": self.sequence,
            "from_state": source,
            "to_state": target,
            "reason": reason,
            "evidence_refs": evidence_refs,
            "occurred_at": utc_now(),
        }
        body["transition_id"] = f"sha256:{canonical_json_sha256(body)}"
        path = self.root / f"{self.sequence:03d}-{target.lower()}.json"
        with path.open("x", encoding="utf-8") as handle:
            json.dump(body, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        return body
