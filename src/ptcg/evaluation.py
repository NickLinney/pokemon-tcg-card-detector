from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .util import canonical_json_sha256


SPLITS = {"train", "development", "evaluation"}
PERMITTED_USES = {"TRAINING", "DEVELOPMENT", "EVALUATION"}


@dataclass(frozen=True)
class GroundTruthRegistry:
    payload: dict[str, Any]

    @classmethod
    def load(cls, path: Path) -> "GroundTruthRegistry":
        value = json.loads(path.resolve(strict=True).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("ground-truth registry must be a JSON object")
        return cls(value)

    @classmethod
    def build(cls, fixtures: list[dict[str, Any]]) -> "GroundTruthRegistry":
        body = {
            "schema_version": "ground-truth-registry-v1",
            "fixtures": fixtures,
        }
        body["registry_id"] = f"sha256:{canonical_json_sha256(body)}"
        return cls(body)

    def validate(self) -> dict[str, Any]:
        findings: list[dict[str, str]] = []
        fixtures = self.payload.get("fixtures")
        if not isinstance(fixtures, list):
            fixtures = []
            findings.append(_finding("FIXTURES_INVALID", "fixtures must be an array"))
        unsigned = {key: value for key, value in self.payload.items() if key != "registry_id"}
        expected = f"sha256:{canonical_json_sha256(unsigned)}"
        if self.payload.get("registry_id") != expected:
            findings.append(_finding("REGISTRY_ID_MISMATCH", "registry identity is invalid"))
        fixture_ids: set[str] = set()
        digest_splits: dict[str, set[str]] = {}
        excluded = {"rights": 0, "truth": 0, "use": 0}
        for index, fixture in enumerate(fixtures):
            if not isinstance(fixture, dict):
                findings.append(_finding("FIXTURE_INVALID", f"fixture {index} is not an object"))
                continue
            fixture_id = fixture.get("fixture_id")
            digest = fixture.get("content_sha256")
            split = fixture.get("split")
            if not isinstance(fixture_id, str) or not fixture_id:
                findings.append(_finding("FIXTURE_ID_INVALID", f"fixture {index} has no identity"))
            elif fixture_id in fixture_ids:
                findings.append(_finding("FIXTURE_ID_DUPLICATE", fixture_id))
            else:
                fixture_ids.add(fixture_id)
            if not isinstance(digest, str) or len(digest) != 64:
                findings.append(_finding("CONTENT_DIGEST_INVALID", str(fixture_id)))
            if split not in SPLITS:
                findings.append(_finding("SPLIT_INVALID", str(fixture_id)))
            elif isinstance(digest, str):
                digest_splits.setdefault(digest, set()).add(split)
            if fixture.get("rights_state") != "APPROVED":
                excluded["rights"] += 1
            if fixture.get("annotation_state") != "ADJUDICATED":
                excluded["truth"] += 1
            if fixture.get("permitted_use") not in PERMITTED_USES:
                excluded["use"] += 1
        for digest, splits in digest_splits.items():
            if len(splits) > 1:
                findings.append(
                    _finding(
                        "SPLIT_LEAKAGE",
                        f"sha256:{digest} occurs across {sorted(splits)}",
                    )
                )
        return {
            "registry_id": self.payload.get("registry_id"),
            "status": "PASS" if not findings else "FAIL",
            "fixture_count": len(fixtures),
            "qualified_count": len(self.qualified()),
            "excluded": excluded,
            "findings": findings,
        }

    def qualified(self, *, split: str | None = None, permitted_use: str | None = None) -> list[dict[str, Any]]:
        result = []
        for fixture in self.payload.get("fixtures", []):
            if not isinstance(fixture, dict):
                continue
            if fixture.get("rights_state") != "APPROVED":
                continue
            if fixture.get("annotation_state") != "ADJUDICATED":
                continue
            if fixture.get("permitted_use") not in PERMITTED_USES:
                continue
            if split is not None and fixture.get("split") != split:
                continue
            if permitted_use is not None and fixture.get("permitted_use") != permitted_use:
                continue
            result.append(fixture)
        return result


def _finding(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}
