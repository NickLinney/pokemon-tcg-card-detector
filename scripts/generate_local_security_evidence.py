#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ptcg.supply_chain import generate_local_security_evidence  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--image-digest")
    args = parser.parse_args()
    result = generate_local_security_evidence(
        ROOT,
        args.output,
        git_commit=args.git_commit,
        image_digest=args.image_digest,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["secret_scan_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
