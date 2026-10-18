from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .util import canonical_json_sha256, ensure_write_path, sha256_file, utc_now


def backup_state(databases: dict[str, Path], output_directory: Path) -> dict[str, Any]:
    output_directory = ensure_write_path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=False)
    entries = []
    for role, source in sorted(databases.items()):
        source = source.resolve(strict=True)
        destination = output_directory / f"{role}.sqlite3"
        with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as source_connection:
            with sqlite3.connect(destination) as destination_connection:
                source_connection.backup(destination_connection)
        integrity = _sqlite_integrity(destination)
        if integrity != "ok":
            raise RuntimeError(f"backup integrity failed for {role}: {integrity}")
        entries.append(
            {
                "role": role,
                "filename": destination.name,
                "sha256": sha256_file(destination),
                "bytes": destination.stat().st_size,
                "sqlite_integrity": integrity,
            }
        )
    body = {
        "schema_version": "local-state-backup-manifest-v1",
        "created_at": utc_now(),
        "databases": entries,
        "retention_policy": "RETAIN_UNTIL_EXPLICITLY_GOVERNED",
    }
    body["manifest_id"] = f"sha256:{canonical_json_sha256(body)}"
    (output_directory / "backup-manifest.json").write_text(
        json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return body


def verify_backup(directory: Path) -> dict[str, Any]:
    directory = directory.resolve(strict=True)
    manifest_path = directory / "backup-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_id"}
    findings = []
    if manifest.get("manifest_id") != f"sha256:{canonical_json_sha256(unsigned)}":
        findings.append("manifest identity mismatch")
    for entry in manifest.get("databases", []):
        path = (directory / entry["filename"]).resolve(strict=True)
        if path.parent != directory:
            findings.append(f"path escape: {entry['role']}")
            continue
        if sha256_file(path) != entry["sha256"]:
            findings.append(f"digest mismatch: {entry['role']}")
        if path.stat().st_size != entry["bytes"]:
            findings.append(f"length mismatch: {entry['role']}")
        if _sqlite_integrity(path) != "ok":
            findings.append(f"sqlite integrity failure: {entry['role']}")
    return {
        "manifest_id": manifest.get("manifest_id"),
        "status": "PASS" if not findings else "FAIL",
        "database_count": len(manifest.get("databases", [])),
        "findings": findings,
    }


def restore_database(backup_database: Path, destination: Path) -> Path:
    backup_database = backup_database.resolve(strict=True)
    destination = ensure_write_path(destination)
    if destination.exists():
        raise FileExistsError("restore destination must be new")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{backup_database}?mode=ro", uri=True) as source:
        with sqlite3.connect(destination) as target:
            source.backup(target)
    if _sqlite_integrity(destination) != "ok":
        raise RuntimeError("restored database failed SQLite integrity")
    return destination


def _sqlite_integrity(path: Path) -> str:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        row = connection.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"
