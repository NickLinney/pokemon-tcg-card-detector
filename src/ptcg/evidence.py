from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from .util import canonical_json_bytes, ensure_write_path, sha256_bytes, sha256_file


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ArtifactIntegrityError(RuntimeError):
    """Raised when immutable artifact bytes no longer match their identity."""


class ContentAddressedArtifactStore:
    """Local immutable artifact store keyed only by SHA-256 content identity."""

    def __init__(self, root: Path):
        self.root = ensure_write_path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put_file(
        self,
        source: Path,
        *,
        media_type: str = "application/octet-stream",
        role: str,
        max_bytes: int = 128 * 1024 * 1024,
    ) -> dict[str, Any]:
        source = source.resolve(strict=True)
        incoming = self.root / ".incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        digest = hashlib.sha256()
        size = 0
        try:
            with source.open("rb") as source_handle, tempfile.NamedTemporaryFile(
                mode="wb", dir=incoming, prefix="artifact-", delete=False
            ) as destination_handle:
                temporary_path = Path(destination_handle.name)
                while chunk := source_handle.read(1024 * 1024):
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError(f"artifact exceeds bounded size of {max_bytes} bytes")
                    digest.update(chunk)
                    destination_handle.write(chunk)
                destination_handle.flush()
                os.fsync(destination_handle.fileno())
            digest_value = digest.hexdigest()
            destination = self._path_for(digest_value)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                self._verify_path(destination, digest_value)
                temporary_path.unlink()
            else:
                os.replace(temporary_path, destination)
            temporary_path = None
            return self._reference(digest_value, size, media_type, role, destination)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def put_json(self, value: Any, *, role: str) -> dict[str, Any]:
        return self.put_bytes(
            canonical_json_bytes(value) + b"\n",
            media_type="application/json",
            role=role,
        )

    def put_bytes(
        self,
        value: bytes,
        *,
        media_type: str = "application/octet-stream",
        role: str,
    ) -> dict[str, Any]:
        digest = sha256_bytes(value)
        destination = self._path_for(digest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            self._verify_path(destination, digest)
        else:
            temporary_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    dir=destination.parent,
                    prefix=".incoming-",
                    delete=False,
                ) as handle:
                    temporary_path = Path(handle.name)
                    handle.write(value)
                    handle.flush()
                    os.fsync(handle.fileno())
                if sha256_file(temporary_path) != digest:
                    raise ArtifactIntegrityError("temporary artifact hash mismatch")
                os.replace(temporary_path, destination)
                temporary_path = None
            finally:
                if temporary_path is not None and temporary_path.exists():
                    temporary_path.unlink()
        return self._reference(digest, len(value), media_type, role, destination)

    def read_verified(self, digest: str) -> bytes:
        path = self._path_for(digest)
        self._verify_path(path, digest)
        return path.read_bytes()

    def verify(self, digest: str) -> dict[str, Any]:
        path = self._path_for(digest)
        self._verify_path(path, digest)
        return {"sha256": digest, "bytes": path.stat().st_size, "status": "VERIFIED"}

    def _path_for(self, digest: str) -> Path:
        if not _SHA256.fullmatch(digest):
            raise ValueError("artifact digest must be 64 lowercase hexadecimal characters")
        return self.root / "sha256" / digest[:2] / digest

    def _reference(
        self,
        digest: str,
        size: int,
        media_type: str,
        role: str,
        destination: Path,
    ) -> dict[str, Any]:
        return {
            "artifact_id": f"sha256:{digest}",
            "sha256": digest,
            "bytes": size,
            "media_type": media_type,
            "role": role,
            "path": str(destination.relative_to(self.root.parent)),
            "immutable": True,
        }

    @staticmethod
    def _verify_path(path: Path, digest: str) -> None:
        if not path.is_file():
            raise ArtifactIntegrityError(f"artifact is missing: sha256:{digest}")
        actual = sha256_file(path)
        if actual != digest:
            raise ArtifactIntegrityError(
                f"artifact hash mismatch: expected sha256:{digest}, observed sha256:{actual}"
            )
