from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .util import canonical_json_sha256, ensure_write_path, sha256_file, utc_now
from .workflow import validate_collection_context


JOB_SCHEMA_VERSION = "analysis-job-v1"
JOB_TRANSITION_SCHEMA_VERSION = "job-transition-v1"


class JobNotFound(KeyError):
    pass


class IdempotencyConflict(ValueError):
    pass


class IllegalJobTransition(ValueError):
    pass


ALLOWED_JOB_TRANSITIONS = {
    "REQUESTED": {"ADMITTED", "REJECTED"},
    "ADMITTED": {"RUNNING", "CANCEL_REQUESTED", "REJECTED", "RECOVERY_REQUIRED"},
    "RUNNING": {"SUCCEEDED", "FAILED", "CANCEL_REQUESTED", "RECOVERY_REQUIRED"},
    "CANCEL_REQUESTED": {"CANCELED", "SUCCEEDED", "FAILED"},
    "RECOVERY_REQUIRED": {"ADMITTED", "CANCELED", "FAILED"},
    "SUCCEEDED": set(),
    "FAILED": set(),
    "CANCELED": set(),
    "REJECTED": set(),
}


class JobStore:
    """SQLite-backed append-only job state and idempotency ledger."""

    def __init__(self, database_path: Path):
        self.database_path = ensure_write_path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def create_or_get(
        self,
        *,
        source_path: Path,
        context: dict[str, Any],
        idempotency_key: str,
    ) -> tuple[dict[str, Any], bool]:
        context = validate_collection_context(context)
        source_path = source_path.resolve(strict=True)
        source_sha256 = sha256_file(source_path)
        key_sha256 = canonical_json_sha256({"idempotency_key": idempotency_key})
        request_sha256 = canonical_json_sha256(
            {"source_sha256": source_sha256, "context": context}
        )
        now = utc_now()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM analysis_jobs WHERE idempotency_key_sha256 = ?",
                (key_sha256,),
            ).fetchone()
            if existing is not None:
                job = self._decode(existing)
                if job["request_sha256"] != request_sha256:
                    raise IdempotencyConflict(
                        "Idempotency-Key was already used with different input or context"
                    )
                return self._public(job), False

            job_id = f"job-{uuid4().hex}"
            connection.execute(
                """
                INSERT INTO analysis_jobs (
                    job_id, state, context_json, source_path, source_sha256,
                    idempotency_key_sha256, request_sha256, run_id, error_json,
                    created_at, updated_at
                ) VALUES (?, 'REQUESTED', ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
                """,
                (
                    job_id,
                    json.dumps(context, ensure_ascii=False, sort_keys=True),
                    str(source_path),
                    source_sha256,
                    key_sha256,
                    request_sha256,
                    now,
                    now,
                ),
            )
            self._append_transition(
                connection, job_id, 1, None, "REQUESTED", "request durably recorded", now
            )
            self._transition_in_transaction(
                connection, job_id, "ADMITTED", "request admitted for local execution"
            )
            row = connection.execute(
                "SELECT * FROM analysis_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        return self._public(self._decode(row)), True

    def get(self, job_id: str, *, internal: bool = False) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM analysis_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if row is None:
            raise JobNotFound(job_id)
        decoded = self._decode(row)
        return decoded if internal else self._public(decoded)

    def transition(
        self,
        job_id: str,
        target: str,
        *,
        reason: str,
        run_id: str | None = None,
        error: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._connect() as connection:
            self._transition_in_transaction(
                connection, job_id, target, reason, run_id=run_id, error=error
            )
            row = connection.execute(
                "SELECT * FROM analysis_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        return self._public(self._decode(row))

    def transitions(self, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM analysis_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if exists is None:
                raise JobNotFound(job_id)
            rows = connection.execute(
                "SELECT * FROM job_transitions WHERE job_id = ? ORDER BY sequence",
                (job_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _transition_in_transaction(
        self,
        connection: sqlite3.Connection,
        job_id: str,
        target: str,
        reason: str,
        *,
        run_id: str | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        row = connection.execute(
            "SELECT state FROM analysis_jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        if row is None:
            raise JobNotFound(job_id)
        source = row["state"]
        if target not in ALLOWED_JOB_TRANSITIONS.get(source, set()):
            raise IllegalJobTransition(f"illegal job transition: {source} -> {target}")
        sequence = connection.execute(
            "SELECT COUNT(*) FROM job_transitions WHERE job_id = ?", (job_id,)
        ).fetchone()[0] + 1
        now = utc_now()
        self._append_transition(connection, job_id, sequence, source, target, reason, now)
        connection.execute(
            """
            UPDATE analysis_jobs
            SET state = ?, run_id = COALESCE(?, run_id), error_json = ?, updated_at = ?
            WHERE job_id = ?
            """,
            (
                target,
                run_id,
                json.dumps(error, ensure_ascii=False, sort_keys=True) if error else None,
                now,
                job_id,
            ),
        )

    @staticmethod
    def _append_transition(
        connection: sqlite3.Connection,
        job_id: str,
        sequence: int,
        source: str | None,
        target: str,
        reason: str,
        occurred_at: str,
    ) -> None:
        body = {
            "schema_version": JOB_TRANSITION_SCHEMA_VERSION,
            "job_id": job_id,
            "sequence": sequence,
            "from_state": source,
            "to_state": target,
            "reason": reason,
            "occurred_at": occurred_at,
        }
        transition_id = f"sha256:{canonical_json_sha256(body)}"
        connection.execute(
            "INSERT INTO job_transitions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                transition_id,
                job_id,
                sequence,
                source,
                target,
                reason,
                occurred_at,
                JOB_TRANSITION_SCHEMA_VERSION,
            ),
        )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS analysis_jobs (
                    job_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    idempotency_key_sha256 TEXT NOT NULL UNIQUE,
                    request_sha256 TEXT NOT NULL,
                    run_id TEXT,
                    error_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS job_transitions (
                    transition_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    UNIQUE(job_id, sequence),
                    FOREIGN KEY(job_id) REFERENCES analysis_jobs(job_id)
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        value = dict(row)
        value["context"] = json.loads(value.pop("context_json"))
        value["error"] = json.loads(value.pop("error_json")) if value["error_json"] else None
        return value

    @staticmethod
    def _public(job: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": JOB_SCHEMA_VERSION,
            "job_id": job["job_id"],
            "state": job["state"],
            "context": job["context"],
            "source_sha256": job["source_sha256"],
            "idempotency_key_sha256": job["idempotency_key_sha256"],
            "run_id": job["run_id"],
            "error": job["error"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        }


class JobService:
    def __init__(
        self,
        store: JobStore,
        analyzer: Callable[..., dict[str, Any]],
        *,
        database_path: Path,
        template_root: Path,
        output_root: Path,
        ocr_mode: str,
        model_directory: Path,
        download_ocr_models: bool = False,
    ):
        self.store = store
        self.analyzer = analyzer
        self.analysis_database_path = database_path
        self.template_root = template_root
        self.output_root = output_root
        self.ocr_mode = ocr_mode
        self.model_directory = model_directory
        self.download_ocr_models = download_ocr_models

    def run(self, job_id: str) -> None:
        job = self.store.get(job_id, internal=True)
        self.store.transition(job_id, "RUNNING", reason="worker claimed admitted job")
        try:
            result = self.analyzer(
                Path(job["source_path"]),
                self.analysis_database_path,
                self.template_root,
                self.output_root,
                ocr_mode=self.ocr_mode,
                download_ocr_models=self.download_ocr_models,
                model_directory=self.model_directory,
                idempotency_key=job["idempotency_key_sha256"],
                context=job["context"],
            )
        except Exception as exc:
            self.store.transition(
                job_id,
                "FAILED",
                reason="analysis worker failed",
                error={"type": type(exc).__name__, "message": str(exc)},
            )
            return
        self.store.transition(
            job_id,
            "SUCCEEDED",
            reason="run manifest and required outputs sealed",
            run_id=result["run_id"],
        )
