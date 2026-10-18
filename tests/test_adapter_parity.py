import inspect
from pathlib import Path

from ptcg import api, cli, service


def test_python_cli_http_share_one_analysis_service_contract():
    parameters = inspect.signature(service.analyze_page_request).parameters
    assert {"image_path", "database_path", "template_root", "output_parent"} <= set(
        parameters
    )
    assert {"context", "idempotency_key", "cancel_check", "symbol_provider"} <= set(
        parameters
    )
    assert cli.analyze_page_request is service.analyze_page_request
    assert api.analyze_page_request is service.analyze_page_request


def test_container_profile_is_loopback_non_root_and_uses_durable_stores():
    root = Path(__file__).parents[1]
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    compose = (root / "compose.yaml").read_text(encoding="utf-8")
    assert "USER 10001:10001" in dockerfile
    assert "127.0.0.1:8080:8080" in compose
    assert "PTCG_JOB_DATABASE" in compose
    assert "PTCG_REVIEW_DATABASE" in compose
    assert "PTCG_REVIEW_TOKEN: ${PTCG_REVIEW_TOKEN:-}" in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "cap_drop:" in compose
