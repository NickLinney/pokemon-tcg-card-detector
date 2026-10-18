import json
from pathlib import Path

import pytest

from ptcg.audit import verify_run
from ptcg.evidence import ContentAddressedArtifactStore
from ptcg.pipeline import _read_idempotent_result
from ptcg.run_control import RunLedger, RunManifest


def _valid_run(tmp_path: Path) -> Path:
    run = tmp_path / "run-fixture"
    run.mkdir()
    (run / "evidence").mkdir()
    manifest = RunManifest.build(
        source_sha256="a" * 64,
        corpus_sha256="b" * 64,
        template_registry_sha256="c" * 64,
        pipeline_version="fixture",
        ocr_provider="none",
        schema_versions={"fixture": "v1"},
        configuration={"offline": True},
    )
    store = ContentAddressedArtifactStore(run / "artifacts")
    artifact = store.put_bytes(b"fixture", role="fixture")
    manifest.payload["source_artifact"] = artifact
    (run / "run-manifest.json").write_text(
        json.dumps(manifest.payload), encoding="utf-8"
    )
    ledger = RunLedger(
        run / "transitions", run_id=run.name, manifest_id=manifest.payload["manifest_id"]
    )
    ledger.transition("ADMITTED", reason="fixture")
    ledger.transition("INGESTED", reason="fixture")
    return run


def test_integrity_audit_verifies_manifest_artifacts_and_transitions(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    result = verify_run(_valid_run(tmp_path))
    assert result["status"] == "PASS"
    assert result["verified_artifact_count"] == 1
    assert result["terminal_state"] == "INGESTED"


def test_integrity_audit_fails_on_tampered_artifact(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    run = _valid_run(tmp_path)
    artifact = next((run / "artifacts" / "sha256").glob("*/*"))
    artifact.write_bytes(b"tampered")
    result = verify_run(run)
    assert result["status"] == "FAIL"
    assert {finding["code"] for finding in result["findings"]} == {
        "ARTIFACT_HASH_MISMATCH"
    }


def test_integrity_audit_fails_on_tampered_transition(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    run = _valid_run(tmp_path)
    transition_path = sorted((run / "transitions").glob("*.json"))[1]
    transition = json.loads(transition_path.read_text(encoding="utf-8"))
    transition["reason"] = "tampered"
    transition_path.write_text(json.dumps(transition), encoding="utf-8")
    result = verify_run(run)
    assert result["status"] == "FAIL"
    assert "TRANSITION_ID_MISMATCH" in {
        finding["code"] for finding in result["findings"]
    }


def test_idempotent_replay_refuses_tampered_completed_run(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    run = _valid_run(tmp_path)
    manifest = RunManifest(
        json.loads((run / "run-manifest.json").read_text(encoding="utf-8"))
    )
    (run / "page-summary.json").write_text(
        json.dumps({"run_id": run.name, "run_state": "INGESTED"}), encoding="utf-8"
    )
    artifact = next((run / "artifacts" / "sha256").glob("*/*"))
    artifact.write_bytes(b"tampered")

    with pytest.raises(ValueError, match="failed integrity verification"):
        _read_idempotent_result(run, manifest)
