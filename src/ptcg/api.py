from __future__ import annotations

import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from uuid import uuid4

from flask import Flask, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from .pipeline import PIPELINE_VERSION
from .jobs import CapacityExceeded, IdempotencyConflict, JobNotFound, JobService, JobStore
from .service import analyze_page_request
from .template_registry import TemplateRegistry
from .util import canonical_json_sha256, ensure_write_path, project_root
from .version import version_metadata
from .workflow import validate_collection_context


ALLOWED_IMAGE_SUFFIXES = {".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
DEFAULT_MAX_CONTENT_LENGTH = 25 * 1024 * 1024


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Create the optional HTTP transport around the shared analysis service."""
    repository_root = Path(__file__).resolve().parents[2]
    root = project_root()
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_PATH=os.environ.get("PTCG_DATABASE"),
        TEMPLATE_ROOT=os.environ.get("PTCG_TEMPLATE_ROOT", str(repository_root / "templates")),
        OUTPUT_ROOT=os.environ.get("PTCG_OUTPUT_ROOT", str(root / ".local" / "runs")),
        UPLOAD_ROOT=os.environ.get("PTCG_UPLOAD_ROOT", str(root / ".local" / "uploads")),
        OCR_MODE=os.environ.get("PTCG_OCR", "easyocr"),
        DOWNLOAD_OCR_MODELS=_environment_boolean("PTCG_DOWNLOAD_OCR_MODELS", False),
        MODEL_DIRECTORY=os.environ.get(
            "PTCG_MODEL_DIRECTORY", str(root / ".models" / "easyocr")
        ),
        JOB_DATABASE=os.environ.get(
            "PTCG_JOB_DATABASE", str(root / ".local" / "jobs" / "jobs.sqlite3")
        ),
        JOB_WORKERS=int(os.environ.get("PTCG_JOB_WORKERS", "1")),
        MAX_ACTIVE_JOBS=int(os.environ.get("PTCG_MAX_ACTIVE_JOBS", "4")),
        RECOVER_JOBS=_environment_boolean("PTCG_RECOVER_JOBS", True),
        MAX_CONTENT_LENGTH=int(
            os.environ.get("PTCG_MAX_CONTENT_LENGTH", DEFAULT_MAX_CONTENT_LENGTH)
        ),
    )
    if config:
        app.config.update(config)

    job_store = JobStore(Path(app.config["JOB_DATABASE"]))
    app.extensions["ptcg_job_store"] = job_store
    app.extensions["ptcg_job_service"] = JobService(
        job_store,
        analyze_page_request,
        database_path=Path(app.config["DATABASE_PATH"]) if app.config.get("DATABASE_PATH") else Path("."),
        template_root=Path(app.config["TEMPLATE_ROOT"]),
        output_root=Path(app.config["OUTPUT_ROOT"]),
        ocr_mode=app.config["OCR_MODE"],
        model_directory=Path(app.config["MODEL_DIRECTORY"]),
        download_ocr_models=bool(app.config["DOWNLOAD_OCR_MODELS"]),
    )
    if app.config["RECOVER_JOBS"]:
        app.extensions["ptcg_jobs_to_recover"] = job_store.recover_interrupted()

    @app.get("/healthz")
    def health() -> tuple[Any, int]:
        return jsonify(status="ok", pipeline_version=PIPELINE_VERSION, **version_metadata()), 200

    @app.get("/v1/meta")
    def metadata() -> tuple[Any, int]:
        return jsonify(pipeline_version=PIPELINE_VERSION, **version_metadata()), 200

    @app.get("/readyz")
    def readiness() -> tuple[Any, int]:
        findings = _readiness_findings(app)
        status = 200 if not findings else 503
        return jsonify(status="ready" if not findings else "not_ready", findings=findings), status

    @app.errorhandler(RequestEntityTooLarge)
    def content_too_large(_error: RequestEntityTooLarge) -> tuple[Any, int]:
        return jsonify(error="content_too_large", message="request body exceeds configured limit"), 413

    @app.post("/v1/pages/analyze")
    def analyze() -> tuple[Any, int]:
        findings = _readiness_findings(app)
        if findings:
            return jsonify(error="service_not_ready", findings=findings), 503

        uploaded = request.files.get("image")
        if uploaded is None or not uploaded.filename:
            return jsonify(error="missing_image", message="multipart field 'image' is required"), 400
        filename = secure_filename(uploaded.filename)
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_IMAGE_SUFFIXES:
            return jsonify(error="unsupported_image_type", allowed=sorted(ALLOWED_IMAGE_SUFFIXES)), 415

        idempotency_key = request.headers.get("Idempotency-Key")
        if idempotency_key is not None and not 1 <= len(idempotency_key) <= 256:
            return jsonify(
                error="invalid_idempotency_key",
                message="Idempotency-Key must contain between 1 and 256 characters",
            ), 400

        request_id = uuid4().hex
        upload_root = ensure_write_path(Path(app.config["UPLOAD_ROOT"]))
        request_directory = ensure_write_path(upload_root / request_id)
        request_directory.mkdir(parents=True, exist_ok=False)
        image_path = request_directory / f"source{suffix}"
        uploaded.save(image_path)

        try:
            result = analyze_page_request(
                image_path,
                Path(app.config["DATABASE_PATH"]),
                Path(app.config["TEMPLATE_ROOT"]),
                Path(app.config["OUTPUT_ROOT"]),
                ocr_mode=app.config["OCR_MODE"],
                download_ocr_models=bool(app.config["DOWNLOAD_OCR_MODELS"]),
                model_directory=Path(app.config["MODEL_DIRECTORY"]),
                idempotency_key=idempotency_key,
            )
        except (FileNotFoundError, ValueError) as exc:
            return jsonify(error="invalid_analysis_request", message=str(exc), request_id=request_id), 400
        except Exception:
            app.logger.exception("page analysis failed; request_id=%s", request_id)
            return jsonify(error="analysis_failed", request_id=request_id), 500
        return jsonify(request_id=request_id, result=result), 200

    @app.post("/v1/analysis-jobs")
    def create_analysis_job() -> tuple[Any, int]:
        findings = _readiness_findings(app)
        if findings:
            return jsonify(error="service_not_ready", findings=findings), 503
        uploaded = request.files.get("image")
        if uploaded is None or not uploaded.filename:
            return jsonify(error="missing_image", message="multipart field 'image' is required"), 400
        filename = secure_filename(uploaded.filename)
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_IMAGE_SUFFIXES:
            return jsonify(error="unsupported_image_type", allowed=sorted(ALLOWED_IMAGE_SUFFIXES)), 415
        idempotency_key = request.headers.get("Idempotency-Key")
        if idempotency_key is None or not 1 <= len(idempotency_key) <= 256:
            return jsonify(
                error="invalid_idempotency_key",
                message="Idempotency-Key must contain between 1 and 256 characters",
            ), 400
        try:
            context = validate_collection_context(
                {
                    "collection_id": request.form.get("collection_id"),
                    "binder_id": request.form.get("binder_id"),
                    "page_id": request.form.get("page_id")
                    or f"page-{canonical_json_sha256({'idempotency_key': idempotency_key})[:12]}",
                    "source_captured_at": request.form.get("source_captured_at"),
                }
            )
        except ValueError as exc:
            return jsonify(error="invalid_collection_context", message=str(exc)), 400

        request_id = uuid4().hex
        request_directory = ensure_write_path(Path(app.config["UPLOAD_ROOT"]) / request_id)
        request_directory.mkdir(parents=True, exist_ok=False)
        image_path = request_directory / f"source{suffix}"
        uploaded.save(image_path)
        try:
            job, created = job_store.create_or_get(
                source_path=image_path,
                context=context,
                idempotency_key=idempotency_key,
                max_active_jobs=int(app.config["MAX_ACTIVE_JOBS"]),
            )
        except CapacityExceeded as exc:
            response = jsonify(error="capacity_exceeded", message=str(exc))
            response.headers["Retry-After"] = str(exc.retry_after)
            return response, 429
        except IdempotencyConflict as exc:
            return jsonify(error="idempotency_conflict", message=str(exc)), 409
        if created:
            _launch_job(app, job["job_id"])
        response = dict(job)
        response["status_url"] = f"/v1/analysis-jobs/{job['job_id']}"
        response["idempotent_replay"] = not created
        return jsonify(response), 202

    @app.get("/v1/analysis-jobs/<job_id>")
    def get_analysis_job(job_id: str) -> tuple[Any, int]:
        try:
            job = job_store.get(job_id)
        except JobNotFound:
            return jsonify(error="job_not_found"), 404
        response = dict(job)
        response["transitions"] = job_store.transitions(job_id)
        if job["run_id"]:
            response["run_url"] = f"/v1/runs/{job['run_id']}"
        return jsonify(response), 200

    @app.post("/v1/analysis-jobs/<job_id>:cancel")
    def cancel_analysis_job(job_id: str) -> tuple[Any, int]:
        try:
            job = job_store.cancel(job_id)
        except JobNotFound:
            return jsonify(error="job_not_found"), 404
        response = dict(job)
        response["status_url"] = f"/v1/analysis-jobs/{job_id}"
        return jsonify(response), 200

    for job_id in app.extensions.get("ptcg_jobs_to_recover", []):
        _launch_job(app, job_id)
    return app


def _launch_job(app: Flask, job_id: str) -> None:
    executor = app.extensions.get("ptcg_job_executor")
    if executor is None:
        executor = ThreadPoolExecutor(
            max_workers=int(app.config["JOB_WORKERS"]),
            thread_name_prefix="ptcg-job",
        )
        app.extensions["ptcg_job_executor"] = executor
    executor.submit(app.extensions["ptcg_job_service"].run, job_id)


def _readiness_findings(app: Flask) -> list[str]:
    findings: list[str] = []
    database_value = app.config.get("DATABASE_PATH")
    if not database_value:
        findings.append("PTCG_DATABASE is not configured")
    else:
        database = Path(database_value)
        if not database.is_file():
            findings.append(f"database is not a file: {database}")

    template_root = Path(app.config["TEMPLATE_ROOT"])
    if not template_root.is_dir():
        findings.append(f"template root is not a directory: {template_root}")
    else:
        findings.extend(f"template registry: {item}" for item in TemplateRegistry(template_root).validate())

    for key in ("OUTPUT_ROOT", "UPLOAD_ROOT"):
        try:
            ensure_write_path(Path(app.config[key]))
        except (FileNotFoundError, ValueError) as exc:
            findings.append(f"{key}: {exc}")
    if app.config.get("OCR_MODE") not in {"easyocr", "none"}:
        findings.append("PTCG_OCR must be 'easyocr' or 'none'")
    return findings


def _environment_boolean(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    if value.casefold() in {"1", "true", "yes", "on"}:
        return True
    if value.casefold() in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ptcg-api")
    parser.add_argument("--host", default=os.environ.get("PTCG_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PTCG_API_PORT", "8080")))
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)
    create_app().run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
