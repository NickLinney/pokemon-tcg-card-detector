from pathlib import Path

from ptcg.api import create_app


def _configured_app(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    database = tmp_path / "cards.sqlite3"
    database.write_bytes(b"fixture")
    template_root = Path(__file__).parents[1] / "templates"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(database),
            "TEMPLATE_ROOT": str(template_root),
            "OUTPUT_ROOT": str(tmp_path / "runs"),
            "UPLOAD_ROOT": str(tmp_path / "uploads"),
            "JOB_DATABASE": str(tmp_path / "jobs" / "jobs.sqlite3"),
            "RECOVER_JOBS": False,
            "MAX_ACTIVE_JOBS": 4,
            "OCR_MODE": "none",
        }
    )
    return app


def test_health_does_not_require_runtime_dependencies(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    response = app.test_client().get("/healthz")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert response.get_json()["canonical_version"] == "0.2.0-pre-alpha.2"
    assert response.get_json()["released"] is False


def test_metadata_preserves_lifecycle_and_distribution_mapping(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    response = app.test_client().get("/v1/meta")
    assert response.status_code == 200
    assert response.get_json() == {
        "canonical_version": "0.2.0-pre-alpha.2",
        "lifecycle": "PRE_ALPHA",
        "pipeline_version": "pre-alpha-evidence-architecture-v7",
        "python_distribution_version": "0.2.0.dev2",
        "released": False,
    }


def test_readiness_reports_missing_database(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    app.config["DATABASE_PATH"] = str(tmp_path / "missing.sqlite3")
    response = app.test_client().get("/readyz")
    assert response.status_code == 503
    assert response.get_json()["status"] == "not_ready"


def test_analysis_requires_multipart_image(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    response = app.test_client().post("/v1/pages/analyze")
    assert response.status_code == 400
    assert response.get_json()["error"] == "missing_image"


def test_analysis_rejects_oversized_body_as_json(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    app.config["MAX_CONTENT_LENGTH"] = 4
    response = app.test_client().post(
        "/v1/pages/analyze",
        data={"image": (bytes_io(b"too large"), "binder.jpeg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 413
    assert response.get_json()["error"] == "content_too_large"


def test_analysis_rejects_oversized_idempotency_key(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    response = app.test_client().post(
        "/v1/pages/analyze",
        data={"image": (bytes_io(b"not-a-real-image"), "binder.jpeg")},
        content_type="multipart/form-data",
        headers={"Idempotency-Key": "x" * 257},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_idempotency_key"


def test_analysis_uses_shared_service_and_preserves_upload(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    observed = {}

    def fake_analyze(image_path, database_path, template_root, output_parent, **kwargs):
        observed.update(
            image_path=image_path,
            database_path=database_path,
            template_root=template_root,
            output_parent=output_parent,
            kwargs=kwargs,
        )
        return {"run_id": "fixture-run"}

    monkeypatch.setattr("ptcg.api.analyze_page_request", fake_analyze)
    response = app.test_client().post(
        "/v1/pages/analyze",
        data={"image": (bytes_io(b"not-a-real-image"), "binder.jpeg")},
        content_type="multipart/form-data",
        headers={"Idempotency-Key": "fixture-request"},
    )
    assert response.status_code == 200
    assert response.get_json()["result"]["run_id"] == "fixture-run"
    assert observed["image_path"].read_bytes() == b"not-a-real-image"
    assert observed["kwargs"]["ocr_mode"] == "none"
    assert observed["kwargs"]["idempotency_key"] == "fixture-request"


def test_async_submission_returns_durable_job_and_replays_idempotently(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    launched = []
    monkeypatch.setattr("ptcg.api._launch_job", lambda _app, job_id: launched.append(job_id))
    client = app.test_client()

    def submit():
        return client.post(
            "/v1/analysis-jobs",
            data={
                "image": (bytes_io(b"fixture-image"), "binder.jpeg"),
                "collection_id": "collection-1",
                "binder_id": "binder-1",
                "page_id": "page-1",
            },
            content_type="multipart/form-data",
            headers={"Idempotency-Key": "request-1"},
        )

    first = submit()
    assert first.status_code == 202
    assert first.get_json()["state"] == "ADMITTED"
    assert first.get_json()["idempotent_replay"] is False
    assert launched == [first.get_json()["job_id"]]

    replay = submit()
    assert replay.status_code == 202
    assert replay.get_json()["job_id"] == first.get_json()["job_id"]
    assert replay.get_json()["idempotent_replay"] is True
    assert launched == [first.get_json()["job_id"]]

    status = client.get(first.get_json()["status_url"])
    assert status.status_code == 200
    assert [item["to_state"] for item in status.get_json()["transitions"]] == [
        "REQUESTED",
        "ADMITTED",
    ]


def test_async_submission_rejects_conflicting_idempotency_key(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    monkeypatch.setattr("ptcg.api._launch_job", lambda _app, job_id: None)
    client = app.test_client()
    base = {
        "collection_id": "collection-1",
        "binder_id": "binder-1",
        "page_id": "page-1",
    }
    first = client.post(
        "/v1/analysis-jobs",
        data={**base, "image": (bytes_io(b"first"), "binder.jpeg")},
        content_type="multipart/form-data",
        headers={"Idempotency-Key": "same-key"},
    )
    assert first.status_code == 202
    conflict = client.post(
        "/v1/analysis-jobs",
        data={**base, "image": (bytes_io(b"different"), "binder.jpeg")},
        content_type="multipart/form-data",
        headers={"Idempotency-Key": "same-key"},
    )
    assert conflict.status_code == 409
    assert conflict.get_json()["error"] == "idempotency_conflict"


def test_async_submission_rejects_context_paths(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    response = app.test_client().post(
        "/v1/analysis-jobs",
        data={
            "image": (bytes_io(b"fixture"), "binder.jpeg"),
            "collection_id": "../escape",
            "binder_id": "binder-1",
        },
        content_type="multipart/form-data",
        headers={"Idempotency-Key": "request-1"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid_collection_context"


def test_cancel_is_idempotent_and_capacity_is_bounded(tmp_path: Path, monkeypatch):
    app = _configured_app(tmp_path, monkeypatch)
    app.config["MAX_ACTIVE_JOBS"] = 1
    monkeypatch.setattr("ptcg.api._launch_job", lambda _app, job_id: None)
    client = app.test_client()

    def submit(key: str):
        return client.post(
            "/v1/analysis-jobs",
            data={
                "image": (bytes_io(key.encode()), "binder.jpeg"),
                "collection_id": "collection-1",
                "binder_id": "binder-1",
                "page_id": key,
            },
            content_type="multipart/form-data",
            headers={"Idempotency-Key": key},
        )

    first = submit("page-1")
    assert first.status_code == 202
    overloaded = submit("page-2")
    assert overloaded.status_code == 429
    assert overloaded.headers["Retry-After"] == "5"

    cancel_url = f"/v1/analysis-jobs/{first.get_json()['job_id']}:cancel"
    canceled = client.post(cancel_url)
    assert canceled.status_code == 200
    assert canceled.get_json()["state"] == "CANCEL_REQUESTED"
    repeated = client.post(cancel_url)
    assert repeated.status_code == 200
    assert repeated.get_json()["state"] == "CANCEL_REQUESTED"


def bytes_io(value: bytes):
    from io import BytesIO

    return BytesIO(value)
