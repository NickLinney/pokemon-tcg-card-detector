#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ptcg.api import create_app  # noqa: E402
from ptcg.util import ensure_write_path, utc_now  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args()

    work_root = ensure_write_path(args.work_root)
    work_root.mkdir(parents=True, exist_ok=False)
    token = "ephemeral-local-uat-token"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(args.corpus.resolve(strict=True)),
            "TEMPLATE_ROOT": str(ROOT / "templates"),
            "OUTPUT_ROOT": str(work_root / "runs"),
            "UPLOAD_ROOT": str(work_root / "uploads"),
            "JOB_DATABASE": str(work_root / "jobs.sqlite3"),
            "REVIEW_DATABASE": str(work_root / "reviews.sqlite3"),
            "REVIEW_TOKEN": token,
            "OCR_MODE": "none",
            "DOWNLOAD_OCR_MODELS": False,
            "RECOVER_JOBS": False,
            "JOB_WORKERS": 1,
            "MAX_ACTIVE_JOBS": 2,
        }
    )
    client = app.test_client()
    with args.image.resolve(strict=True).open("rb") as handle:
        submitted = client.post(
            "/v1/analysis-jobs",
            data={
                "image": (handle, args.image.name),
                "collection_id": "pre-alpha-uat",
                "binder_id": "binder-1",
                "page_id": "page-1",
            },
            content_type="multipart/form-data",
            headers={"Idempotency-Key": f"uat-{args.git_commit}"},
        )
    if submitted.status_code != 202:
        return _finish(args.report, {"status": "FAIL", "stage": "submit", "response": submitted.get_json()})
    job = submitted.get_json()
    deadline = time.monotonic() + args.timeout_seconds
    while time.monotonic() < deadline:
        current = client.get(job["status_url"])
        if current.status_code != 200:
            return _finish(args.report, {"status": "FAIL", "stage": "job-status"})
        job = current.get_json()
        if job["state"] in {"SUCCEEDED", "FAILED", "CANCELED", "REJECTED"}:
            break
        time.sleep(0.05)
    else:
        return _finish(args.report, {"status": "FAIL", "stage": "timeout"})
    if job["state"] != "SUCCEEDED":
        return _finish(args.report, {"status": "FAIL", "stage": "analysis", "job": job})

    run = client.get(job["run_url"])
    artifacts = client.get(f"{job['run_url']}/artifacts")
    if run.status_code != 200 or artifacts.status_code != 200:
        return _finish(args.report, {"status": "FAIL", "stage": "artifact-enumeration"})
    index = artifacts.get_json()
    inventory = next(
        item for item in index["artifacts"] if item["role"] == "inventory-csv"
    )
    downloaded = client.get(f"{job['run_url']}/artifacts/{inventory['artifact_id']}")
    digest_matches = hashlib.sha256(downloaded.data).hexdigest() == inventory["sha256"]

    queue = client.get("/v1/reviews?state=required&limit=100").get_json()
    review = queue["items"][0]
    disposition = client.post(
        f"/v1/reviews/{review['review_id']}/dispositions",
        json={
            "action": "LEAVE_UNRESOLVED",
            "reason": "UAT verifies mechanics only; approved identity truth is unavailable.",
            "evidence_version": review["evidence_version"],
            "expected_prior_assertion": None,
        },
        headers={
            "Authorization": f"Bearer {token}",
            "X-PTCG-Actor": "local:uat-reviewer",
            "X-PTCG-Authority-Scope": "pre-alpha-uat",
        },
    )
    projection = client.get("/v1/inventories/pre-alpha-uat")
    executor = app.extensions.get("ptcg_job_executor")
    if executor is not None:
        executor.shutdown(wait=True)
    result = {
        "schema_version": "pre-alpha-local-uat-result-v1",
        "status": (
            "PASS_QUALIFIED"
            if digest_matches and disposition.status_code == 201 and projection.status_code == 200
            else "FAIL"
        ),
        "git_commit": args.git_commit,
        "executed_at": utc_now(),
        "job_state": job["state"],
        "job_transition_states": [item["to_state"] for item in job["transitions"]],
        "run_id": run.get_json()["run_id"],
        "run_state": run.get_json()["run_state"],
        "artifact_count": len(index["artifacts"]),
        "inventory_csv_sha256": inventory["sha256"],
        "inventory_download_digest_matches": digest_matches,
        "review_required_count": queue["total"],
        "review_action": disposition.get_json().get("action") if disposition.is_json else None,
        "effective_projection_items": len(projection.get_json()["items"]),
        "uat_15_artifact_download": "PASS" if digest_matches else "FAIL",
        "uat_14_finalized_inventory": "FAIL_EVIDENCE_REQUIRED",
        "uat_14_reason": "No rights-qualified, adjudicated identity truth was supplied; no identity was asserted.",
        "automatic_confirmation": "PROHIBITED",
        "release_authorized": False,
    }
    return _finish(args.report, result)


def _finish(report_path: Path, result: dict) -> int:
    report_path = ensure_write_path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS_QUALIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
