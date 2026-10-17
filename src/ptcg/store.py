from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class ReferenceStore:
    def __init__(self, database_path: Path):
        self.connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def candidates(
        self,
        *,
        series_id: str | None = None,
        set_id: str | None = None,
        category: str | None = None,
        hp: int | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("series_id", series_id),
            ("set_id", set_id),
            ("category", category),
            ("hp", hp),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        sql = "SELECT * FROM reference_cards"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY set_id, local_id LIMIT ?"
        params.append(limit)
        return [self._decode(row) for row in self.connection.execute(sql, params)]

    def by_id(self, canonical_reference_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM reference_cards WHERE canonical_reference_id = ?",
            (canonical_reference_id,),
        ).fetchone()
        return self._decode(row) if row else None

    def media_for(self, canonical_reference_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM reference_media WHERE canonical_reference_id = ?",
            (canonical_reference_id,),
        )
        return [dict(row) for row in rows]

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        for field in (
            "names_json",
            "normalized_names_json",
            "types_json",
            "dex_ids_json",
            "attacks_json",
            "abilities_json",
            "variants_json",
            "mapped_fields_json",
            "unmapped_fields_json",
        ):
            payload[field.removesuffix("_json")] = json.loads(payload.pop(field))
        payload.pop("source_payload", None)
        return payload
