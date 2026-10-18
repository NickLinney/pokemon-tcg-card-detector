import json
from pathlib import Path

from ptcg.evidence import ContentAddressedArtifactStore
from ptcg.reviews import ReviewStore
from ptcg.run_catalog import seal_artifact_index


def build_review_run(tmp_path: Path) -> Path:
    run = tmp_path / "runs" / "run-review-fixture"
    run.mkdir(parents=True)
    store = ContentAddressedArtifactStore(run / "artifacts")
    evidence = store.put_bytes(
        b'{"evidence":"fixture"}\n',
        media_type="application/json",
        role="card-evidence-payload:pocket-01",
    )
    summary = {
        "run_id": run.name,
        "collection_context": {
            "collection_id": "collection-1",
            "binder_id": "binder-1",
            "page_id": "page-1",
        },
        "cards": [
            {
                "pocket_index": 1,
                "decision": {
                    "state": "AMBIGUOUS",
                    "human_review_required": True,
                },
                "evidence_artifact": evidence,
                "template_classification": {"unknown_family": False},
                "zone_coverage": {"observed_records": 19},
                "top_candidates": [
                    {"reference_card_id": "tcgdex:sv1:001", "score": 0.7}
                ],
            },
            {
                "pocket_index": 2,
                "decision": {
                    "state": "NO_REFERENCE_MATCH",
                    "human_review_required": False,
                },
                "evidence_artifact": evidence,
                "top_candidates": [],
            },
        ],
        "nonclaims": ["fixture does not establish accuracy"],
    }
    (run / "page-summary.json").write_text(json.dumps(summary), encoding="utf-8")
    seal_artifact_index(
        run,
        [
            {
                **evidence,
                "safe_filename": "pocket-01-evidence.json",
                "downloadable": True,
            }
        ],
    )
    return run


def test_review_queue_is_derived_from_decision_truth(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    run = build_review_run(tmp_path)
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    review_ids = store.index_run(run)
    assert len(review_ids) == 1
    page = store.list(state="REQUIRED")
    assert page["total"] == 1
    review = store.get(review_ids[0])
    assert review["state"] == "REQUIRED"
    assert review["decision"]["state"] == "AMBIGUOUS"
    assert review["candidate_refs"] == ["tcgdex:sv1:001"]
    assert review["artifact_refs"] == [review["evidence_version"]]


def test_review_indexing_is_idempotent(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    run = build_review_run(tmp_path)
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    assert store.index_run(run) == store.index_run(run)
    assert store.list()["total"] == 1


def test_disposition_is_attributable_append_only_and_candidate_bound(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    store = ReviewStore(tmp_path / "reviews.sqlite3")
    review_id = store.index_run(build_review_run(tmp_path))[0]
    evidence_version = store.get(review_id)["evidence_version"]
    disposition = store.append_disposition(
        review_id,
        actor_id="local:reviewer-1",
        authority_scope="collection-1",
        payload={
            "action": "SELECT_CANDIDATE",
            "reason": "Reviewed evidence supports the candidate.",
            "identity_assertion": {"reference_card_id": "tcgdex:sv1:001"},
            "printing_assertion": None,
            "field_correction": None,
            "evidence_version": evidence_version,
            "expected_prior_assertion": None,
        },
    )
    assert disposition["disposition_id"].startswith("sha256:")
    assert store.get(review_id)["state"] == "RESOLVED"
    assert store.dispositions(review_id) == [disposition]
