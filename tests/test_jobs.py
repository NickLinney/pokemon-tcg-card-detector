from pathlib import Path

import pytest

from ptcg.jobs import CapacityExceeded, IdempotencyConflict, IllegalJobTransition, JobStore


def test_job_store_is_durable_append_only_and_hides_raw_key(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    source = tmp_path / "source.jpeg"
    source.write_bytes(b"image")
    database = tmp_path / "jobs.sqlite3"
    context = {"collection_id": "c1", "binder_id": "b1", "page_id": "p1"}
    store = JobStore(database)
    job, created = store.create_or_get(
        source_path=source, context=context, idempotency_key="secret-caller-key"
    )
    assert created is True
    assert job["state"] == "ADMITTED"
    assert "secret-caller-key" not in database.read_bytes().decode("latin-1")

    reopened = JobStore(database)
    assert reopened.get(job["job_id"])["state"] == "ADMITTED"
    assert [item["to_state"] for item in reopened.transitions(job["job_id"])] == [
        "REQUESTED",
        "ADMITTED",
    ]
    reopened.transition(job["job_id"], "RUNNING", reason="test worker")
    reopened.transition(job["job_id"], "SUCCEEDED", reason="sealed", run_id="run-1")
    assert reopened.get(job["job_id"])["run_id"] == "run-1"
    with pytest.raises(IllegalJobTransition):
        reopened.transition(job["job_id"], "RUNNING", reason="cannot reopen terminal")


def test_job_store_rejects_idempotency_conflict(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    first = tmp_path / "first.jpeg"
    second = tmp_path / "second.jpeg"
    first.write_bytes(b"one")
    second.write_bytes(b"two")
    store = JobStore(tmp_path / "jobs.sqlite3")
    context = {"collection_id": "c1", "binder_id": "b1", "page_id": "p1"}
    store.create_or_get(source_path=first, context=context, idempotency_key="same")
    with pytest.raises(IdempotencyConflict):
        store.create_or_get(source_path=second, context=context, idempotency_key="same")


def test_recovery_requeues_running_and_finishes_recorded_cancel(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    source = tmp_path / "source.jpeg"
    source.write_bytes(b"image")
    store = JobStore(tmp_path / "jobs.sqlite3")
    context = {"collection_id": "c1", "binder_id": "b1", "page_id": "p1"}
    running, _ = store.create_or_get(
        source_path=source, context=context, idempotency_key="running"
    )
    store.transition(running["job_id"], "RUNNING", reason="worker")
    canceling, _ = store.create_or_get(
        source_path=source, context=context, idempotency_key="canceling"
    )
    store.transition(canceling["job_id"], "CANCEL_REQUESTED", reason="operator")

    reopened = JobStore(tmp_path / "jobs.sqlite3")
    assert reopened.recover_interrupted() == [running["job_id"]]
    assert reopened.get(running["job_id"])["state"] == "ADMITTED"
    assert reopened.get(canceling["job_id"])["state"] == "CANCELED"
    assert [item["to_state"] for item in reopened.transitions(running["job_id"])][-2:] == [
        "RECOVERY_REQUIRED",
        "ADMITTED",
    ]


def test_capacity_rejection_allows_idempotent_replay(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    source = tmp_path / "source.jpeg"
    source.write_bytes(b"image")
    store = JobStore(tmp_path / "jobs.sqlite3")
    context = {"collection_id": "c1", "binder_id": "b1", "page_id": "p1"}
    first, _ = store.create_or_get(
        source_path=source,
        context=context,
        idempotency_key="one",
        max_active_jobs=1,
    )
    replay, created = store.create_or_get(
        source_path=source,
        context=context,
        idempotency_key="one",
        max_active_jobs=1,
    )
    assert created is False
    assert replay["job_id"] == first["job_id"]
    with pytest.raises(CapacityExceeded):
        store.create_or_get(
            source_path=source,
            context={**context, "page_id": "p2"},
            idempotency_key="two",
            max_active_jobs=1,
        )
