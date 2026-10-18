import sqlite3
from pathlib import Path

from ptcg.operations import backup_state, restore_database, verify_backup


def database(path: Path, value: str) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE state (value TEXT NOT NULL)")
        connection.execute("INSERT INTO state VALUES (?)", (value,))


def test_backup_verify_and_non_overwriting_restore(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    jobs = tmp_path / "jobs.sqlite3"
    reviews = tmp_path / "reviews.sqlite3"
    database(jobs, "job-state")
    database(reviews, "review-state")
    backup = tmp_path / "backup"
    manifest = backup_state({"jobs": jobs, "reviews": reviews}, backup)
    assert manifest["retention_policy"] == "RETAIN_UNTIL_EXPLICITLY_GOVERNED"
    assert verify_backup(backup)["status"] == "PASS"

    restored = restore_database(backup / "jobs.sqlite3", tmp_path / "restore" / "jobs.sqlite3")
    with sqlite3.connect(restored) as connection:
        assert connection.execute("SELECT value FROM state").fetchone()[0] == "job-state"
