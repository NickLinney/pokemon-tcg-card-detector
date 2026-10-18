import json
from pathlib import Path

import pytest

from ptcg.run_control import IllegalRunTransition, RunLedger, RunManifest


def _manifest() -> RunManifest:
    return RunManifest.build(
        source_sha256="a" * 64,
        corpus_sha256="b" * 64,
        template_registry_sha256="c" * 64,
        pipeline_version="fixture-v1",
        ocr_provider="none",
        schema_versions={"zone": "v2"},
        configuration={"offline": True},
        idempotency_key="fixture-key",
    )


def test_run_manifest_identity_is_deterministic_and_key_is_not_retained():
    first = _manifest()
    second = _manifest()
    assert first.digest == second.digest
    assert first.payload["bindings"]["idempotency_key_sha256"]
    assert first.payload["bindings"]["product_version"] == "0.2.0-pre-alpha.2"
    assert first.payload["bindings"]["lifecycle"] == "PRE_ALPHA"
    assert "fixture-key" not in json.dumps(first.payload)


def test_run_ledger_enforces_state_machine_and_appends(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    ledger = RunLedger(tmp_path / "transitions", run_id="run-1", manifest_id=_manifest().payload["manifest_id"])
    ledger.transition("ADMITTED", reason="fixture")
    ledger.transition("INGESTED", reason="fixture")
    assert ledger.state == "INGESTED"
    assert len(list((tmp_path / "transitions").glob("*.json"))) == 3

    with pytest.raises(IllegalRunTransition, match="illegal"):
        ledger.transition("DECIDED", reason="skip prerequisites")
