from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .util import canonical_json_sha256, ensure_write_path, sha256_file, utc_now
from .version import CANONICAL_VERSION, LIFECYCLE


LOCK_ENTRY = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s]+)$")
SECRET_PATTERNS = {
    "PRIVATE_KEY": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GITHUB_TOKEN": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "AWS_ACCESS_KEY": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}


def generate_local_security_evidence(
    repository_root: Path,
    output_directory: Path,
    *,
    git_commit: str,
    image_digest: str | None = None,
) -> dict[str, Any]:
    repository_root = repository_root.resolve(strict=True)
    output_directory = ensure_write_path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=False)
    lock_path = repository_root / "requirements-runtime.lock.txt"
    components = []
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        match = LOCK_ENTRY.fullmatch(line.strip())
        if match:
            components.append(
                {
                    "type": "library",
                    "name": match.group(1),
                    "version": match.group(2),
                    "purl": f"pkg:pypi/{match.group(1).lower()}@{match.group(2)}",
                    "licenses": [{"license": {"id": "NOASSERTION"}}],
                }
            )
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "pokemon-tcg-card-detector",
                "version": CANONICAL_VERSION,
            }
        },
        "components": sorted(components, key=lambda item: item["name"].casefold()),
    }
    sbom_path = output_directory / "sbom.cdx.json"
    sbom_path.write_text(
        json.dumps(sbom, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    secret_findings = scan_repository_secrets(repository_root)
    secret_report = {
        "schema_version": "local-secret-scan-v1",
        "scope": "tracked-source-shaped files excluding .git, caches and local state",
        "status": "PASS" if not secret_findings else "FAIL",
        "findings": secret_findings,
        "nonclaim": "Pattern scan is not a substitute for an independent secret-scanning gate.",
    }
    secret_path = output_directory / "secret-scan.json"
    secret_path.write_text(
        json.dumps(secret_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    provenance = {
        "schema_version": "local-candidate-provenance-v1",
        "product_version": CANONICAL_VERSION,
        "lifecycle": LIFECYCLE,
        "git_commit": git_commit,
        "image_digest": image_digest,
        "runtime_lock_sha256": sha256_file(lock_path),
        "dependency_license_register_sha256": sha256_file(
            repository_root / "docs" / "DEPENDENCY-LICENSE-REGISTER.md"
        ),
        "sbom_sha256": sha256_file(sbom_path),
        "secret_scan_sha256": sha256_file(secret_path),
        "vulnerability_scan_state": "EVIDENCE_REQUIRED",
        "container_scan_state": "EVIDENCE_REQUIRED" if image_digest is None else "NOT_EXECUTED",
        "generated_at": utc_now(),
        "release_authorized": False,
    }
    provenance["provenance_id"] = f"sha256:{canonical_json_sha256(provenance)}"
    provenance_path = output_directory / "provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "sbom": str(sbom_path),
        "secret_scan": str(secret_path),
        "provenance": str(provenance_path),
        "provenance_id": provenance["provenance_id"],
        "secret_scan_status": secret_report["status"],
        "vulnerability_scan_state": "EVIDENCE_REQUIRED",
        "release_authorized": False,
    }


def scan_repository_secrets(repository_root: Path) -> list[dict[str, Any]]:
    findings = []
    excluded = {".git", ".pytest_cache", "__pycache__", ".local", ".models"}
    text_suffixes = {
        ".md", ".py", ".toml", ".txt", ".yaml", ".yml", ".json", ".csv", ".ini"
    }
    for path in sorted(repository_root.rglob("*")):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        if path.suffix.casefold() not in text_suffixes and path.name not in {
            "Dockerfile", "LICENSE"
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "rule": name,
                        "path": str(path.relative_to(repository_root)),
                        "line": text.count("\n", 0, match.start()) + 1,
                    }
                )
    return findings
