from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from .run_control import ALLOWED_TRANSITIONS
from .util import canonical_json_sha256, sha256_file


def verify_run(run_directory: Path) -> dict[str, Any]:
    run_directory = run_directory.resolve(strict=True)
    findings: list[dict[str, str]] = []
    manifest_path = run_directory / "run-manifest.json"
    if not manifest_path.is_file():
        findings.append(_finding("MANIFEST_MISSING", "run-manifest.json is missing"))
        manifest: dict[str, Any] = {}
    else:
        manifest = _load_json(manifest_path, findings)
        bindings = manifest.get("bindings")
        if isinstance(bindings, dict):
            expected = f"sha256:{canonical_json_sha256(bindings)}"
            if manifest.get("manifest_id") != expected:
                findings.append(
                    _finding("MANIFEST_ID_MISMATCH", "manifest identity does not match bindings")
                )
        else:
            findings.append(_finding("MANIFEST_BINDINGS_INVALID", "manifest bindings are absent"))

    artifact_files = sorted((run_directory / "artifacts" / "sha256").glob("*/*"))
    verified_artifacts = 0
    for path in artifact_files:
        if not path.is_file():
            continue
        expected = path.name
        actual = sha256_file(path)
        if actual != expected:
            findings.append(
                _finding(
                    "ARTIFACT_HASH_MISMATCH",
                    f"{path.relative_to(run_directory)} expected {expected}, observed {actual}",
                )
            )
        else:
            verified_artifacts += 1

    evidence_documents = sorted((run_directory / "evidence").glob("*.json"))
    referenced_artifacts: set[str] = set()
    for path in evidence_documents:
        payload = _load_json(path, findings)
        referenced_artifacts.update(_artifact_digests(payload))
    referenced_artifacts.update(_artifact_digests(manifest))
    stored_artifacts = {path.name for path in artifact_files if path.is_file()}
    for digest in sorted(referenced_artifacts - stored_artifacts):
        findings.append(
            _finding("DANGLING_ARTIFACT_REFERENCE", f"referenced sha256:{digest} is not stored")
        )

    transitions = []
    for path in sorted((run_directory / "transitions").glob("*.json")):
        payload = _load_json(path, findings)
        if payload:
            transitions.append(payload)
            referenced_artifacts.update(_artifact_digests(payload))
    previous: str | None = None
    for index, transition in enumerate(transitions, start=1):
        if transition.get("sequence") != index:
            findings.append(_finding("TRANSITION_SEQUENCE_GAP", f"expected sequence {index}"))
        source = transition.get("from_state")
        target = transition.get("to_state")
        recorded_transition_id = transition.get("transition_id")
        transition_body = {
            key: value for key, value in transition.items() if key != "transition_id"
        }
        expected_transition_id = f"sha256:{canonical_json_sha256(transition_body)}"
        if recorded_transition_id != expected_transition_id:
            findings.append(
                _finding(
                    "TRANSITION_ID_MISMATCH",
                    f"transition sequence {index} identity does not match its content",
                )
            )
        if transition.get("manifest_id") != manifest.get("manifest_id"):
            findings.append(
                _finding(
                    "TRANSITION_MANIFEST_MISMATCH",
                    f"transition sequence {index} is bound to a different manifest",
                )
            )
        if index == 1:
            if source is not None or target != "REQUESTED":
                findings.append(_finding("TRANSITION_ROOT_INVALID", "first transition is not REQUESTED"))
        else:
            if source != previous or target not in ALLOWED_TRANSITIONS.get(source, set()):
                findings.append(
                    _finding("TRANSITION_INVALID", f"invalid transition {source} -> {target}")
                )
        previous = target

    for digest in sorted(stored_artifacts - referenced_artifacts):
        findings.append(
            _finding("ORPHAN_ARTIFACT", f"stored sha256:{digest} has no manifest/evidence reference")
        )

    return {
        "schema_version": "run-integrity-audit-v1",
        "run_id": run_directory.name,
        "status": "PASS" if not findings else "FAIL",
        "manifest_id": manifest.get("manifest_id"),
        "terminal_state": previous,
        "verified_artifact_count": verified_artifacts,
        "referenced_artifact_count": len(referenced_artifacts),
        "transition_count": len(transitions),
        "evidence_document_count": len(evidence_documents),
        "findings": findings,
        "nonclaims": [
            "Integrity verification does not establish model accuracy.",
            "A passing audit is not a production or release approval.",
        ],
    }


def _load_json(path: Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(_finding("JSON_INVALID", f"{path.name}: {exc}"))
        return {}
    if not isinstance(payload, dict):
        findings.append(_finding("JSON_OBJECT_REQUIRED", f"{path.name} is not an object"))
        return {}
    return payload


def _artifact_digests(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        artifact_id = value.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id.startswith("sha256:"):
            yield artifact_id.removeprefix("sha256:")
        for nested in value.values():
            yield from _artifact_digests(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _artifact_digests(nested)


def _finding(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}
