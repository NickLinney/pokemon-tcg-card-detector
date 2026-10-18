from pathlib import Path

import pytest

from ptcg.evidence import ArtifactIntegrityError, ContentAddressedArtifactStore


def test_content_addressed_store_deduplicates_and_verifies(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    store = ContentAddressedArtifactStore(tmp_path / "run" / "artifacts")
    first = store.put_bytes(b"same evidence", role="fixture")
    second = store.put_bytes(b"same evidence", role="independent-provenance")

    assert first["artifact_id"] == second["artifact_id"]
    assert first["role"] != second["role"]
    assert store.read_verified(first["sha256"]) == b"same evidence"


def test_content_addressed_store_detects_corruption(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    store = ContentAddressedArtifactStore(tmp_path / "run" / "artifacts")
    reference = store.put_bytes(b"original", role="fixture")
    artifact_path = tmp_path / "run" / reference["path"]
    artifact_path.write_bytes(b"corrupt")

    with pytest.raises(ArtifactIntegrityError, match="hash mismatch"):
        store.read_verified(reference["sha256"])


def test_artifact_lookup_rejects_path_like_digest(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    store = ContentAddressedArtifactStore(tmp_path / "run" / "artifacts")
    with pytest.raises(ValueError, match="digest"):
        store.read_verified("../../outside")


def test_streaming_file_put_enforces_bound_and_cleans_temporary_file(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    source = tmp_path / "source.bin"
    source.write_bytes(b"12345")
    store = ContentAddressedArtifactStore(tmp_path / "run" / "artifacts")
    with pytest.raises(ValueError, match="bounded size"):
        store.put_file(source, role="fixture", max_bytes=4)
    assert list((tmp_path / "run" / "artifacts" / ".incoming").iterdir()) == []
