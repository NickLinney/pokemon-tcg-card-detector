from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .util import canonical_json_sha256, sha256_file, utc_now, write_json_new


RUN_ID = re.compile(r"^run-[A-Za-z0-9-]{1,120}$")
ARTIFACT_INDEX_SCHEMA_VERSION = "run-artifact-index-v1"


class RunNotFound(KeyError):
    pass


class RunNotSealed(RuntimeError):
    pass


class ArtifactNotFound(KeyError):
    pass


class ArtifactIntegrityFailure(RuntimeError):
    pass


def seal_artifact_index(
    run_directory: Path,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    descriptors = []
    for artifact in artifacts:
        descriptors.append(
            {
                "schema_version": "artifact-descriptor-v1",
                "artifact_id": artifact["artifact_id"],
                "run_id": run_directory.name,
                "sha256": artifact["sha256"],
                "bytes": artifact["bytes"],
                "media_type": artifact["media_type"],
                "role": artifact["role"],
                "safe_filename": artifact["safe_filename"],
                "path": artifact["path"],
                "downloadable": bool(artifact.get("downloadable", True)),
            }
        )
    descriptors.sort(key=lambda value: (value["role"], value["safe_filename"]))
    body = {
        "schema_version": ARTIFACT_INDEX_SCHEMA_VERSION,
        "run_id": run_directory.name,
        "state": "SEALED",
        "artifacts": descriptors,
        "sealed_at": utc_now(),
    }
    body["artifact_index_id"] = f"sha256:{canonical_json_sha256(body)}"
    write_json_new(run_directory / "artifact-index.json", body)
    return body


class RunCatalog:
    """Read only sealed run summaries and manifest-backed artifacts."""

    def __init__(self, output_root: Path):
        self.output_root = output_root.resolve()

    def summary(self, run_id: str) -> dict[str, Any]:
        run = self._run_directory(run_id)
        summary = self._load_json(run / "page-summary.json", unsealed=True)
        index = self._load_index(run)
        return {
            "run_id": run_id,
            "run_state": summary.get("run_state"),
            "run_manifest_id": summary.get("run_manifest_id"),
            "pipeline_version": summary.get("pipeline_version"),
            "collection_context": summary.get("collection_context"),
            "decision_counts": summary.get("decision_counts", {}),
            "artifact_index_id": index["artifact_index_id"],
            "artifact_count": len(index["artifacts"]),
            "artifacts_url": f"/v1/runs/{run_id}/artifacts",
        }

    def artifacts(self, run_id: str) -> dict[str, Any]:
        run = self._run_directory(run_id)
        return self._load_index(run)

    def resolve_artifact(self, run_id: str, artifact_id: str) -> tuple[dict[str, Any], Path]:
        run = self._run_directory(run_id)
        index = self._load_index(run)
        descriptor = next(
            (item for item in index["artifacts"] if item["artifact_id"] == artifact_id),
            None,
        )
        if descriptor is None or not descriptor.get("downloadable"):
            raise ArtifactNotFound(artifact_id)
        candidate = (run / descriptor["path"]).resolve(strict=True)
        if os.path.commonpath((str(run), str(candidate))) != str(run):
            raise ArtifactIntegrityFailure("artifact path escapes sealed run")
        if not candidate.is_file() or sha256_file(candidate) != descriptor["sha256"]:
            raise ArtifactIntegrityFailure("artifact bytes do not match sealed descriptor")
        if candidate.stat().st_size != descriptor["bytes"]:
            raise ArtifactIntegrityFailure("artifact length does not match sealed descriptor")
        return descriptor, candidate

    def _run_directory(self, run_id: str) -> Path:
        if not RUN_ID.fullmatch(run_id):
            raise RunNotFound(run_id)
        candidate = (self.output_root / run_id).resolve()
        if os.path.commonpath((str(self.output_root), str(candidate))) != str(self.output_root):
            raise RunNotFound(run_id)
        if not candidate.is_dir():
            raise RunNotFound(run_id)
        return candidate

    def _load_index(self, run: Path) -> dict[str, Any]:
        index = self._load_json(run / "artifact-index.json", unsealed=True)
        if index.get("state") != "SEALED":
            raise RunNotSealed(run.name)
        recorded = index.get("artifact_index_id")
        unsigned = {key: value for key, value in index.items() if key != "artifact_index_id"}
        expected = f"sha256:{canonical_json_sha256(unsigned)}"
        if recorded != expected:
            raise ArtifactIntegrityFailure("artifact index identity mismatch")
        return index

    @staticmethod
    def _load_json(path: Path, *, unsealed: bool) -> dict[str, Any]:
        if not path.is_file():
            if unsealed:
                raise RunNotSealed(path.parent.name)
            raise RunNotFound(path.parent.name)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ArtifactIntegrityFailure(f"invalid JSON: {path.name}") from exc
        if not isinstance(value, dict):
            raise ArtifactIntegrityFailure(f"JSON object required: {path.name}")
        return value
