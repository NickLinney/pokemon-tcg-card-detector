from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .util import ensure_write_path, normalize_text, sha256_file, sha256_text, utc_now, write_json_new


SCHEMA_VERSION = "reference-card-v1"
MAPPED_FIELDS = {
    "abilities",
    "attacks",
    "category",
    "cameoDexIds",
    "description",
    "dexId",
    "effect",
    "evolveFrom",
    "hp",
    "illustrator",
    "item",
    "legal",
    "level",
    "name",
    "rarity",
    "regulationMark",
    "resistances",
    "retreat",
    "set",
    "stage",
    "suffix",
    "thirdParty",
    "trainerType",
    "types",
    "variants",
    "weaknesses",
    "weight",
}


@dataclass(frozen=True)
class ParsedCard:
    canonical_reference_id: str
    source_card_id: str
    series_id: str
    set_id: str
    local_id: str
    category: str | None
    names: dict[str, str]
    hp: int | None
    rarity: str | None
    illustrator: str | None
    stage: str | None
    suffix: str | None
    regulation_mark: str | None
    types: list[str]
    dex_ids: list[int]
    attacks: list[dict[str, Any]]
    abilities: list[dict[str, Any]]
    variants: list[dict[str, Any]]
    source_path: str
    source_payload_hash: str
    source_payload: str
    mapped_fields: list[str]
    unmapped_fields: list[str]


def _block(text: str, key: str, opener: str, closer: str) -> str | None:
    match = re.search(rf"\b{re.escape(key)}\s*:\s*\{opener}", text)
    if not match:
        return None
    start = match.end() - 1
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _string_map(text: str, key: str) -> dict[str, str]:
    block = _block(text, key, "{", "}")
    if not block:
        return {}
    pairs = re.findall(r"\b([a-z]{2}(?:-[a-z]{2})?)\s*:\s*(['\"])(.*?)\2\s*,?", block, re.S)
    return {lang: bytes(value, "utf-8").decode("unicode_escape") if "\\u" in value else value for lang, _, value in pairs}


def _scalar(text: str, key: str) -> str | int | None:
    match = re.search(rf"\b{re.escape(key)}\s*:\s*(?:(['\"])(.*?)\1|(-?\d+))", text, re.S)
    if not match:
        return None
    return match.group(2) if match.group(2) is not None else int(match.group(3))


def _string_array(text: str, key: str) -> list[str]:
    block = _block(text, key, "[", "]")
    if not block:
        return []
    return [match[1] for match in re.findall(r"(['\"])(.*?)\1", block, re.S)]


def _int_array(text: str, key: str) -> list[int]:
    block = _block(text, key, "[", "]")
    return [int(value) for value in re.findall(r"\b\d+\b", block or "")]


def _object_array(text: str, key: str) -> list[str]:
    block = _block(text, key, "[", "]")
    if not block:
        return []
    objects: list[str] = []
    depth = 0
    start = None
    quote: str | None = None
    escaped = False
    for index, char in enumerate(block):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(block[start : index + 1])
                start = None
    return objects


def _named_records(text: str, key: str) -> list[dict[str, Any]]:
    records = []
    for item in _object_array(text, key):
        records.append(
            {
                "name": _string_map(item, "name"),
                "effect": _string_map(item, "effect"),
                "damage": _scalar(item, "damage"),
                "type": _scalar(item, "type"),
                "cost": _string_array(item, "cost"),
            }
        )
    return records


def _variants(text: str) -> list[dict[str, Any]]:
    return [
        {"type": _scalar(item, "type"), "stamp": _string_array(item, "stamp")}
        for item in _object_array(text, "variants")
    ]


def _top_level_fields(text: str) -> list[str]:
    # The upstream repository formats top-level Card keys with one leading tab.
    return sorted(set(re.findall(r"^\t([A-Za-z][A-Za-z0-9_]*)\s*:", text, re.M)))


def parse_card(path: Path, source_root: Path) -> ParsedCard:
    text = path.read_text(encoding="utf-8")
    local_id = path.stem
    set_file = path.parent.with_suffix(".ts")
    series_file = path.parent.parent.with_suffix(".ts")
    set_text = set_file.read_text(encoding="utf-8") if set_file.exists() else ""
    series_text = series_file.read_text(encoding="utf-8") if series_file.exists() else ""
    set_id = str(_scalar(set_text, "id") or path.parent.name)
    series_id = str(_scalar(series_text, "id") or path.parent.parent.name)
    source_scope = path.relative_to(source_root).parts[0]
    source_id = f"{set_id}-{local_id}"
    fields = _top_level_fields(text)
    return ParsedCard(
        canonical_reference_id=f"tcgdex:{source_scope}:{source_id}",
        source_card_id=source_id,
        series_id=series_id,
        set_id=set_id,
        local_id=local_id,
        category=_scalar(text, "category"),
        names=_string_map(text, "name"),
        hp=_scalar(text, "hp") if isinstance(_scalar(text, "hp"), int) else None,
        rarity=_scalar(text, "rarity"),
        illustrator=_scalar(text, "illustrator"),
        stage=_scalar(text, "stage"),
        suffix=_scalar(text, "suffix"),
        regulation_mark=_scalar(text, "regulationMark"),
        types=_string_array(text, "types"),
        dex_ids=_int_array(text, "dexId"),
        attacks=_named_records(text, "attacks"),
        abilities=_named_records(text, "abilities"),
        variants=_variants(text),
        source_path=str(path.relative_to(source_root)),
        source_payload_hash=sha256_text(text),
        source_payload=text,
        mapped_fields=sorted(set(fields) & MAPPED_FIELDS),
        unmapped_fields=sorted(set(fields) - MAPPED_FIELDS),
    )


def discover_card_files(source_root: Path) -> Iterable[Path]:
    for data_root_name in ("data", "data-asia"):
        data_root = source_root / data_root_name
        if not data_root.exists():
            continue
        for path in sorted(data_root.rglob("*.ts")):
            prefix = path.read_text(encoding="utf-8", errors="ignore")[:500]
            if "const card: Card" in prefix:
                yield path


def source_commit(source_root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True
    ).strip()


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode=DELETE;
        PRAGMA foreign_keys=ON;
        CREATE TABLE snapshots (
          snapshot_id TEXT PRIMARY KEY,
          source_system TEXT NOT NULL,
          repository TEXT NOT NULL,
          source_commit TEXT NOT NULL,
          source_tag TEXT,
          schema_version TEXT NOT NULL,
          license_spdx TEXT NOT NULL,
          license_sha256 TEXT NOT NULL
        );
        CREATE TABLE reference_cards (
          canonical_reference_id TEXT PRIMARY KEY,
          snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id),
          source_card_id TEXT NOT NULL,
          series_id TEXT NOT NULL,
          set_id TEXT NOT NULL,
          local_id TEXT NOT NULL,
          category TEXT,
          names_json TEXT NOT NULL,
          normalized_names_json TEXT NOT NULL,
          hp INTEGER,
          rarity TEXT,
          illustrator TEXT,
          stage TEXT,
          suffix TEXT,
          regulation_mark TEXT,
          types_json TEXT NOT NULL,
          dex_ids_json TEXT NOT NULL,
          attacks_json TEXT NOT NULL,
          abilities_json TEXT NOT NULL,
          variants_json TEXT NOT NULL,
          source_path TEXT NOT NULL,
          source_payload_hash TEXT NOT NULL,
          source_payload TEXT NOT NULL,
          mapped_fields_json TEXT NOT NULL,
          unmapped_fields_json TEXT NOT NULL,
          UNIQUE(snapshot_id, source_path)
        );
        CREATE INDEX idx_cards_source_id ON reference_cards(source_card_id);
        CREATE INDEX idx_cards_set_local ON reference_cards(set_id, local_id);
        CREATE INDEX idx_cards_series ON reference_cards(series_id);
        CREATE INDEX idx_cards_category_hp ON reference_cards(category, hp);
        CREATE INDEX idx_cards_stage ON reference_cards(stage);
        CREATE INDEX idx_cards_regulation ON reference_cards(regulation_mark);
        CREATE INDEX idx_cards_illustrator ON reference_cards(illustrator);
        CREATE TABLE import_errors (
          source_path TEXT NOT NULL,
          error_type TEXT NOT NULL,
          message TEXT NOT NULL
        );
        CREATE TABLE reference_media (
          canonical_reference_id TEXT NOT NULL REFERENCES reference_cards(canonical_reference_id),
          source_uri TEXT,
          local_path TEXT,
          retrieved_at TEXT,
          content_hash TEXT,
          width INTEGER,
          height INTEGER,
          rights_status TEXT NOT NULL,
          rights_note TEXT NOT NULL,
          PRIMARY KEY(canonical_reference_id, source_uri)
        );
        CREATE VIRTUAL TABLE card_names_fts USING fts5(
          canonical_reference_id UNINDEXED,
          language UNINDEXED,
          name,
          normalized_name
        );
        """
    )


def ingest_tcgdex(source_root: Path, database_path: Path, manifest_path: Path) -> dict[str, Any]:
    source_root = source_root.resolve(strict=True)
    database_path = ensure_write_path(database_path)
    manifest_path = ensure_write_path(manifest_path)
    if database_path.exists():
        raise FileExistsError(f"refusing to overwrite existing database: {database_path}")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    commit = source_commit(source_root)
    license_path = source_root / "LICENSE"
    snapshot_id = f"tcgdex:v2.48.0:{commit}"
    connection = sqlite3.connect(database_path)
    _create_schema(connection)
    connection.execute(
        "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            snapshot_id,
            "TCGdex cards-database",
            "https://github.com/tcgdex/cards-database",
            commit,
            "v2.48.0",
            SCHEMA_VERSION,
            "MIT",
            sha256_file(license_path),
        ),
    )
    card_count = 0
    errors: list[dict[str, str]] = []
    unmapped_counts: dict[str, int] = {}
    for path in discover_card_files(source_root):
        try:
            card = parse_card(path, source_root)
            names = card.names
            normalized_names = {lang: normalize_text(name) for lang, name in names.items()}
            values = (
                    card.canonical_reference_id,
                    snapshot_id,
                    card.source_card_id,
                    card.series_id,
                    card.set_id,
                    card.local_id,
                    card.category,
                    json.dumps(names, ensure_ascii=False, sort_keys=True),
                    json.dumps(normalized_names, ensure_ascii=False, sort_keys=True),
                    card.hp,
                    card.rarity,
                    card.illustrator,
                    card.stage,
                    card.suffix,
                    card.regulation_mark,
                    json.dumps(card.types, ensure_ascii=False),
                    json.dumps(card.dex_ids),
                    json.dumps(card.attacks, ensure_ascii=False, sort_keys=True),
                    json.dumps(card.abilities, ensure_ascii=False, sort_keys=True),
                    json.dumps(card.variants, ensure_ascii=False, sort_keys=True),
                    card.source_path,
                    card.source_payload_hash,
                    card.source_payload,
                    json.dumps(card.mapped_fields),
                    json.dumps(card.unmapped_fields),
                )
            connection.execute(
                f"INSERT INTO reference_cards VALUES ({','.join('?' for _ in values)})",
                values,
            )
            for language, name in names.items():
                connection.execute(
                    "INSERT INTO card_names_fts VALUES (?, ?, ?, ?)",
                    (card.canonical_reference_id, language, name, normalize_text(name)),
                )
            for field in card.unmapped_fields:
                unmapped_counts[field] = unmapped_counts.get(field, 0) + 1
            card_count += 1
        except Exception as exc:  # preserve bad source records instead of silently skipping
            error = {
                "source_path": str(path.relative_to(source_root)),
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
            errors.append(error)
            connection.execute(
                "INSERT INTO import_errors VALUES (?, ?, ?)",
                (error["source_path"], error["error_type"], error["message"]),
            )
    connection.commit()
    connection.close()
    manifest = {
        "manifest_version": 1,
        "snapshot_id": snapshot_id,
        "repository": "https://github.com/tcgdex/cards-database",
        "tag": "v2.48.0",
        "commit": commit,
        "acquired_for_project_on": "2026-10-17",
        "license_spdx": "MIT",
        "license_sha256": sha256_file(license_path),
        "schema_version": SCHEMA_VERSION,
        "card_count": card_count,
        "import_error_count": len(errors),
        "errors": errors,
        "unmapped_top_level_field_counts": dict(sorted(unmapped_counts.items())),
        "database_sha256": sha256_file(database_path),
        "database_path": str(database_path),
        "generated_at": utc_now(),
        "media_rights": "separate_from_metadata_license; not established as FLOSS",
    }
    written = write_json_new(manifest_path, manifest)
    manifest["manifest_path"] = str(written)
    return manifest


def verify_database(database_path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    card_count = connection.execute("SELECT count(*) FROM reference_cards").fetchone()[0]
    error_count = connection.execute("SELECT count(*) FROM import_errors").fetchone()[0]
    snapshot = connection.execute(
        "SELECT snapshot_id, source_commit, source_tag, license_spdx FROM snapshots"
    ).fetchone()
    connection.close()
    return {
        "integrity_check": integrity,
        "card_count": card_count,
        "import_error_count": error_count,
        "snapshot": {
            "snapshot_id": snapshot[0],
            "source_commit": snapshot[1],
            "source_tag": snapshot[2],
            "license_spdx": snapshot[3],
        },
        "database_sha256": sha256_file(database_path),
    }
