#!/usr/bin/env python3
"""Fail when governed product-version surfaces disagree."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ptcg.version import CANONICAL_VERSION, PYTHON_DISTRIBUTION_VERSION  # noqa: E402


def main() -> int:
    findings: list[str] = []
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["version"] != PYTHON_DISTRIBUTION_VERSION:
        findings.append("pyproject.toml distribution version differs from ptcg.version")

    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    match = re.search(r"^ARG PTCG_VERSION=(\S+)$", dockerfile, re.MULTILINE)
    if match is None or match.group(1) != CANONICAL_VERSION:
        findings.append("Dockerfile PTCG_VERSION differs from canonical version")

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1
    print(
        f"PASS: canonical={CANONICAL_VERSION} "
        f"python={PYTHON_DISTRIBUTION_VERSION} released=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
