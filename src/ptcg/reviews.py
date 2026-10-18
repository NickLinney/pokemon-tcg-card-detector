from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .util import canonical_json_sha256, ensure_write_path
from .workflow import location_id


class ReviewNotFound(KeyError):
    pass


class ReviewIntegrityFailure(RuntimeError):
    pass


class ReviewStore:
    """Derived review read model; source run evidence remains immutable."""

    def __init__(self, database_path: Path):
        self.database_path = ensure_write_path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def index_run(self, run_directory: Path) -> list[str]:
        run_directory = run_directory.resolve(strict=True)
        summary_path = run_directory / "page-summary.json"
        artifact_index_path = run_directory / "artifact-index.json"
        if not summary_path.is_file() or not artifact_index_path.is_file():
            raise ReviewIntegrityFailure("sealed summary and artifact index are required")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        artifact_index = json.loads(artifact_index_path.read_text(encoding="utf-8"))
        context = summary.get("collection_context")
        if not isinstance(context, dict):
            raise ReviewIntegrityFailure("run summary lacks collection context")
        indexed: list[str] = []
        with self._connect() as connection:
            for card in summary.get("cards", []):
                decision = card.get("decision", {})
                if decision.get("human_review_required") is not True:
                    continue
                pocket_index = card.get("pocket_index")
                evidence_artifact = card.get("evidence_artifact", {})
                evidence_version = evidence_artifact.get("artifact_id")
                if not isinstance(pocket_index, int) or not isinstance(evidence_version, str):
                    raise ReviewIntegrityFailure("review-required card lacks bound evidence")
                stable_location = location_id(context, pocket_index)
                identity = canonical_json_sha256(
                    {
                        "run_id": summary["run_id"],
                        "location_id": stable_location,
                        "evidence_version": evidence_version,
                    }
                )
                review_id = f"review-{identity}"
                read_model = {
                    "schema_version": "review-case-v1",
                    "review_id": review_id,
                    "run_id": summary["run_id"],
                    "location_id": stable_location,
                    "state": "REQUIRED",
                    "evidence_version": evidence_version,
                    "decision": decision,
                    "template_classification": card.get("template_classification", {}),
                    "zone_coverage": card.get("zone_coverage", {}),
                    "candidates": card.get("top_candidates", []),
                    "candidate_refs": [
                        candidate["reference_card_id"]
                        for candidate in card.get("top_candidates", [])
                        if isinstance(candidate.get("reference_card_id"), str)
                    ],
                    "artifact_refs": [
                        item["artifact_id"]
                        for item in artifact_index.get("artifacts", [])
                        if item.get("role") in {
                            f"card-evidence-payload:pocket-{pocket_index:02d}",
                            "page-summary",
                        }
                    ],
                    "limitations": summary.get("nonclaims", []),
                }
                serialized = json.dumps(read_model, ensure_ascii=False, sort_keys=True)
                existing = connection.execute(
                    "SELECT read_model_json FROM review_cases WHERE review_id = ?",
                    (review_id,),
                ).fetchone()
                if existing is not None and existing[0] != serialized:
                    raise ReviewIntegrityFailure("deterministic review identity changed content")
                connection.execute(
                    """
                    INSERT OR IGNORE INTO review_cases (
                        review_id, run_id, location_id, state, evidence_version, read_model_json
                    ) VALUES (?, ?, ?, 'REQUIRED', ?, ?)
                    """,
                    (review_id, summary["run_id"], stable_location, evidence_version, serialized),
                )
                indexed.append(review_id)
        return indexed

    def list(self, *, state: str = "REQUIRED", limit: int = 25, offset: int = 0) -> dict[str, Any]:
        if state not in {"REQUIRED", "RESOLVED", "UNRESOLVED", "RECAPTURE_REQUESTED"}:
            raise ValueError("invalid review state")
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError("invalid pagination")
        with self._connect() as connection:
            total = connection.execute(
                "SELECT COUNT(*) FROM review_cases WHERE state = ?", (state,)
            ).fetchone()[0]
            rows = connection.execute(
                """
                SELECT read_model_json FROM review_cases
                WHERE state = ? ORDER BY review_id LIMIT ? OFFSET ?
                """,
                (state, limit, offset),
            ).fetchall()
        items = [json.loads(row[0]) for row in rows]
        for item in items:
            item["state"] = state
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def get(self, review_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state, read_model_json FROM review_cases WHERE review_id = ?",
                (review_id,),
            ).fetchone()
        if row is None:
            raise ReviewNotFound(review_id)
        value = json.loads(row["read_model_json"])
        value["state"] = row["state"]
        return value

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS review_cases (
                    review_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    location_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    evidence_version TEXT NOT NULL,
                    read_model_json TEXT NOT NULL,
                    UNIQUE(run_id, location_id, evidence_version)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection
