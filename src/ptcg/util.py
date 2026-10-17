from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[\s\-_・·.]+", "", value)
    return value or None


def japanese_character_fraction(value: str) -> float:
    if not value:
        return 0.0
    meaningful = [char for char in value if not char.isspace()]
    if not meaningful:
        return 0.0
    japanese = sum(
        1
        for char in meaningful
        if "\u3040" <= char <= "\u30ff" or "\u3400" <= char <= "\u9fff"
    )
    return japanese / len(meaningful)


def project_root() -> Path:
    configured = os.environ.get("PTCG_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve(strict=True)
    # src/ptcg/util.py -> repository -> authorized Project root
    return Path(__file__).resolve().parents[3]


def ensure_write_path(path: Path, root: Path | None = None) -> Path:
    """Reject writes that escape the authorized root, including symlink parents."""
    root = (root or project_root()).resolve(strict=True)
    candidate = path.expanduser()
    existing = candidate
    suffix: list[str] = []
    while not existing.exists():
        suffix.append(existing.name)
        if existing.parent == existing:
            break
        existing = existing.parent
    resolved = existing.resolve(strict=True)
    for name in reversed(suffix):
        resolved = resolved / name
    if os.path.commonpath((str(root), str(resolved))) != str(root):
        raise ValueError(f"write path escapes authorized Project root: {path}")
    return resolved


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 10_000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not allocate a non-overwriting path for {path}")


def write_json_new(path: Path, payload: Any) -> Path:
    path = unique_path(ensure_write_path(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(serialized, encoding="utf-8")
    return path


def relative_or_absolute(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())
