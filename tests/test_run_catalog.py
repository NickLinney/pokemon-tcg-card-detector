import json
from pathlib import Path

import pytest

from ptcg.evidence import ContentAddressedArtifactStore
from ptcg.run_catalog import (
    ArtifactIntegrityFailure,
    RunCatalog,
    RunNotFound,
    RunNotSealed,
    seal_artifact_index,
)


def _sealed_run(tmp_path: Path, monkeypatch) -> tuple[RunCatalog, str, dict]:
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    runs = tmp_path / "runs"
    run = runs / "run-fixture-1"
    run.mkdir(parents=True)
    (run / "page-summary.json").write_text(
        json.dumps(
            {
                "run_id": run.name,
                "run_state": "REVIEW_REQUIRED",
                "run_manifest_id": "sha256:" + "a" * 64,
                "pipeline_version": "fixture",
                "collection_context": {"collection_id": "c1"},
                "decision_counts": {"AMBIGUOUS": 1},
            }
        ),
        encoding="utf-8",
    )
    store = ContentAddressedArtifactStore(run / "artifacts")
    ref = store.put_bytes(b"a,b\n1,2\n", media_type="text/csv", role="inventory-csv")
    index = seal_artifact_index(
        run,
        [{**ref, "safe_filename": "inventory.csv", "downloadable": True}],
    )
    return RunCatalog(runs), run.name, index


def test_run_catalog_returns_only_sealed_descriptors(tmp_path: Path, monkeypatch):
    catalog, run_id, index = _sealed_run(tmp_path, monkeypatch)
    summary = catalog.summary(run_id)
    assert summary["artifact_index_id"] == index["artifact_index_id"]
    assert summary["artifact_count"] == 1
    assert catalog.artifacts(run_id)["artifacts"][0]["safe_filename"] == "inventory.csv"


def test_run_catalog_distinguishes_unknown_and_unsealed(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    runs = tmp_path / "runs"
    runs.mkdir()
    catalog = RunCatalog(runs)
    with pytest.raises(RunNotFound):
        catalog.summary("run-missing")
    unsealed = runs / "run-unsealed"
    unsealed.mkdir()
    (unsealed / "page-summary.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RunNotSealed):
        catalog.summary("run-unsealed")


def test_run_catalog_rejects_symlink_escape(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    runs = tmp_path / "runs"
    run = runs / "run-symlink"
    run.mkdir(parents=True)
    outside = tmp_path / "outside.csv"
    outside.write_bytes(b"outside")
    (run / "escape").symlink_to(outside)
    from ptcg.util import sha256_file

    digest = sha256_file(outside)
    seal_artifact_index(
        run,
        [
            {
                "artifact_id": f"sha256:{digest}",
                "sha256": digest,
                "bytes": outside.stat().st_size,
                "media_type": "text/csv",
                "role": "inventory-csv",
                "path": "escape",
                "safe_filename": "inventory.csv",
                "downloadable": True,
            }
        ],
    )
    with pytest.raises(ArtifactIntegrityFailure, match="escapes"):
        RunCatalog(runs).resolve_artifact(run.name, f"sha256:{digest}")
