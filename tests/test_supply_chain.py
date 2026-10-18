import json
from pathlib import Path

from ptcg.supply_chain import generate_local_security_evidence, scan_repository_secrets


def test_local_security_evidence_is_exact_and_qualified(tmp_path: Path, monkeypatch):
    project = tmp_path / "project"
    (project / "docs").mkdir(parents=True)
    (project / "requirements-runtime.lock.txt").write_text(
        "Example==1.2.3\n", encoding="utf-8"
    )
    (project / "docs" / "DEPENDENCY-LICENSE-REGISTER.md").write_text(
        "# licenses\n", encoding="utf-8"
    )
    (project / "safe.py").write_text("value = 'not-a-secret'\n", encoding="utf-8")
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    result = generate_local_security_evidence(
        project,
        tmp_path / "evidence",
        git_commit="a" * 40,
    )
    assert result["secret_scan_status"] == "PASS"
    assert result["vulnerability_scan_state"] == "EVIDENCE_REQUIRED"
    provenance = json.loads(Path(result["provenance"]).read_text())
    assert provenance["git_commit"] == "a" * 40
    assert provenance["release_authorized"] is False
    sbom = json.loads(Path(result["sbom"]).read_text())
    assert sbom["components"][0]["purl"] == "pkg:pypi/example@1.2.3"


def test_secret_scan_reports_location_without_echoing_secret(tmp_path: Path):
    (tmp_path / "unsafe.txt").write_text(
        "token = " + "ghp" + "_" + "a" * 32 + "\n", encoding="utf-8"
    )
    findings = scan_repository_secrets(tmp_path)
    assert findings == [{"rule": "GITHUB_TOKEN", "path": "unsafe.txt", "line": 1}]
    assert "ghp_" not in json.dumps(findings)
