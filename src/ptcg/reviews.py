from __future__ import annotations

import json
import re
import sqlite3
import csv
from pathlib import Path
from typing import Any

from .util import canonical_json_sha256, ensure_write_path, utc_now
from .workflow import location_id


class ReviewNotFound(KeyError):
    pass


class ReviewIntegrityFailure(RuntimeError):
    pass


class ReviewConflict(RuntimeError):
    pass


class ReviewValidationError(ValueError):
    pass


ACTOR_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@-]{0,127}$")
REVIEW_ACTIONS = {
    "SELECT_CANDIDATE",
    "MANUAL_ASSERTION",
    "REJECT_ALL",
    "CORRECT_FIELD",
    "REQUEST_RECAPTURE",
    "LEAVE_UNRESOLVED",
}


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
                        review_id, run_id, collection_id, location_id, state,
                        evidence_version, read_model_json
                    ) VALUES (?, ?, ?, ?, 'REQUIRED', ?, ?)
                    """,
                    (
                        review_id,
                        summary["run_id"],
                        context["collection_id"],
                        stable_location,
                        evidence_version,
                        serialized,
                    ),
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
                "SELECT state, read_model_json, current_assertion_id FROM review_cases WHERE review_id = ?",
                (review_id,),
            ).fetchone()
        if row is None:
            raise ReviewNotFound(review_id)
        value = json.loads(row["read_model_json"])
        value["state"] = row["state"]
        value["current_assertion_id"] = row["current_assertion_id"]
        value["dispositions"] = self.dispositions(review_id)
        return value

    def append_disposition(
        self,
        review_id: str,
        *,
        actor_id: str,
        authority_scope: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if not ACTOR_ID.fullmatch(actor_id):
            raise ReviewValidationError("valid attributable actor_id is required")
        if not authority_scope or len(authority_scope) > 256:
            raise ReviewValidationError("bounded authority_scope is required")
        action = payload.get("action")
        reason = payload.get("reason")
        if action not in REVIEW_ACTIONS:
            raise ReviewValidationError("unsupported review action")
        if not isinstance(reason, str) or not 1 <= len(reason) <= 2048:
            raise ReviewValidationError("reason must contain 1-2048 characters")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM review_cases WHERE review_id = ?", (review_id,)
            ).fetchone()
            if row is None:
                raise ReviewNotFound(review_id)
            if payload.get("evidence_version") != row["evidence_version"]:
                raise ReviewConflict("stale or foreign evidence_version")
            expected = payload.get("expected_prior_assertion")
            if expected != row["current_assertion_id"]:
                raise ReviewConflict("expected_prior_assertion does not match effective state")
            read_model = json.loads(row["read_model_json"])
            self._validate_action(action, payload, read_model)
            occurred_at = utc_now()
            body = {
                "schema_version": "review-disposition-v1",
                "review_id": review_id,
                "actor_id": actor_id,
                "authority_scope": authority_scope,
                "action": action,
                "reason": reason,
                "identity_assertion": payload.get("identity_assertion"),
                "printing_assertion": payload.get("printing_assertion"),
                "field_correction": payload.get("field_correction"),
                "evidence_version": row["evidence_version"],
                "expected_prior_assertion": expected,
                "occurred_at": occurred_at,
            }
            body["disposition_id"] = f"sha256:{canonical_json_sha256(body)}"
            connection.execute(
                """
                INSERT INTO review_dispositions (
                    disposition_id, review_id, occurred_at, disposition_json
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    body["disposition_id"],
                    review_id,
                    occurred_at,
                    json.dumps(body, ensure_ascii=False, sort_keys=True),
                ),
            )
            state = {
                "REQUEST_RECAPTURE": "RECAPTURE_REQUESTED",
                "LEAVE_UNRESOLVED": "UNRESOLVED",
            }.get(action, "RESOLVED")
            effective_state = self._effective_state(action, payload, read_model)
            assertion = {
                "schema_version": "superseding-assertion-v1",
                "location_id": row["location_id"],
                "source_disposition_id": body["disposition_id"],
                "supersedes": row["current_assertion_id"],
                "effective_state": effective_state,
                "created_at": occurred_at,
            }
            assertion["assertion_id"] = f"sha256:{canonical_json_sha256(assertion)}"
            connection.execute(
                """
                INSERT INTO superseding_assertions (
                    assertion_id, review_id, collection_id, location_id,
                    created_at, assertion_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    assertion["assertion_id"],
                    review_id,
                    row["collection_id"],
                    row["location_id"],
                    occurred_at,
                    json.dumps(assertion, ensure_ascii=False, sort_keys=True),
                ),
            )
            connection.execute(
                """
                UPDATE review_cases SET state = ?, current_assertion_id = ?
                WHERE review_id = ?
                """,
                (state, assertion["assertion_id"], review_id),
            )
        return body

    def dispositions(self, review_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT disposition_json FROM review_dispositions
                WHERE review_id = ? ORDER BY occurred_at, disposition_id
                """,
                (review_id,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def assertions(self, review_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT assertion_json FROM superseding_assertions
                WHERE review_id = ? ORDER BY created_at, assertion_id
                """,
                (review_id,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def effective_inventory(self, collection_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT a.assertion_json
                FROM review_cases c
                JOIN superseding_assertions a ON a.assertion_id = c.current_assertion_id
                WHERE c.collection_id = ?
                ORDER BY c.location_id
                """,
                (collection_id,),
            ).fetchall()
        items = []
        for row in rows:
            assertion = json.loads(row[0])
            items.append(
                {
                    "location_id": assertion["location_id"],
                    "assertion_id": assertion["assertion_id"],
                    "effective_state": assertion["effective_state"],
                }
            )
        body = {
            "schema_version": "effective-inventory-projection-v1",
            "projection_version": "effective-inventory-projector-v1",
            "collection_id": collection_id,
            "generated_at": utc_now(),
            "items": items,
        }
        body["projection_id"] = f"sha256:{canonical_json_sha256(body)}"
        return body

    def export_effective_inventory(self, collection_id: str, directory: Path) -> dict[str, Path]:
        directory = ensure_write_path(directory)
        directory.mkdir(parents=True, exist_ok=False)
        projection = self.effective_inventory(collection_id)
        rows = [
            {
                "location_id": item["location_id"],
                "assertion_id": item["assertion_id"],
                "effective_state_json": json.dumps(
                    item["effective_state"], ensure_ascii=False, separators=(",", ":"), sort_keys=True
                ),
            }
            for item in projection["items"]
        ]
        jsonl_path = directory / "effective-inventory.jsonl"
        with jsonl_path.open("x", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        csv_path = directory / "effective-inventory.csv"
        with csv_path.open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["location_id", "assertion_id", "effective_state_json"]
            )
            writer.writeheader()
            writer.writerows(rows)
        sqlite_path = directory / "effective-inventory.sqlite3"
        with sqlite3.connect(sqlite_path) as connection:
            connection.execute(
                """
                CREATE TABLE effective_inventory (
                    location_id TEXT PRIMARY KEY,
                    assertion_id TEXT NOT NULL,
                    effective_state_json TEXT NOT NULL
                )
                """
            )
            connection.executemany(
                "INSERT INTO effective_inventory VALUES (?, ?, ?)",
                [tuple(row.values()) for row in rows],
            )
        return {"csv": csv_path, "jsonl": jsonl_path, "sqlite": sqlite_path}

    @staticmethod
    def _effective_state(
        action: str, payload: dict[str, Any], read_model: dict[str, Any]
    ) -> dict[str, Any]:
        state: dict[str, Any] = {
            "review_action": action,
            "automated_decision_state": read_model.get("decision", {}).get("state"),
        }
        if action in {"SELECT_CANDIDATE", "MANUAL_ASSERTION"}:
            state.update(
                identification_state="CONFIRMED_HUMAN",
                canonical_reference_id=payload["identity_assertion"]["reference_card_id"],
                printing_assertion=payload.get("printing_assertion"),
            )
        elif action == "REJECT_ALL":
            state.update(
                identification_state="NO_REFERENCE_MATCH_HUMAN",
                canonical_reference_id=None,
            )
        elif action == "REQUEST_RECAPTURE":
            state.update(identification_state="RECAPTURE_REQUESTED", canonical_reference_id=None)
        elif action == "LEAVE_UNRESOLVED":
            state.update(identification_state="AMBIGUOUS", canonical_reference_id=None)
        else:
            state.update(
                identification_state="FIELD_CORRECTED_HUMAN",
                canonical_reference_id=None,
                field_correction=payload.get("field_correction"),
            )
        return state

    @staticmethod
    def _validate_action(
        action: str, payload: dict[str, Any], read_model: dict[str, Any]
    ) -> None:
        identity = payload.get("identity_assertion")
        printing = payload.get("printing_assertion")
        correction = payload.get("field_correction")
        if action in {"SELECT_CANDIDATE", "MANUAL_ASSERTION"}:
            if not isinstance(identity, dict) or not isinstance(
                identity.get("reference_card_id"), str
            ):
                raise ReviewValidationError("identity_assertion.reference_card_id is required")
            if action == "SELECT_CANDIDATE" and identity["reference_card_id"] not in read_model.get(
                "candidate_refs", []
            ):
                raise ReviewValidationError(
                    "candidate absent from evidence requires MANUAL_ASSERTION"
                )
        if action == "CORRECT_FIELD" and not isinstance(correction, dict):
            raise ReviewValidationError("field_correction is required")
        if printing is not None and not isinstance(printing, dict):
            raise ReviewValidationError("printing_assertion must remain a separate object")

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS review_cases (
                    review_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    collection_id TEXT,
                    location_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    evidence_version TEXT NOT NULL,
                    read_model_json TEXT NOT NULL,
                    current_assertion_id TEXT,
                    UNIQUE(run_id, location_id, evidence_version)
                )
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(review_cases)")
            }
            if "current_assertion_id" not in columns:
                connection.execute(
                    "ALTER TABLE review_cases ADD COLUMN current_assertion_id TEXT"
                )
            if "collection_id" not in columns:
                connection.execute("ALTER TABLE review_cases ADD COLUMN collection_id TEXT")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS review_dispositions (
                    disposition_id TEXT PRIMARY KEY,
                    review_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    disposition_json TEXT NOT NULL,
                    FOREIGN KEY(review_id) REFERENCES review_cases(review_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS superseding_assertions (
                    assertion_id TEXT PRIMARY KEY,
                    review_id TEXT NOT NULL,
                    collection_id TEXT NOT NULL,
                    location_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    assertion_json TEXT NOT NULL,
                    FOREIGN KEY(review_id) REFERENCES review_cases(review_id)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection
