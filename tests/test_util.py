import json
from pathlib import Path

import pytest

from ptcg.util import ensure_write_path, normalize_text, project_root, write_json_new


def test_normalize_text_preserves_japanese_semantics():
    assert normalize_text(" ハヤト・の ピジョット ") == "ハヤトのピジョット"


def test_write_guard_rejects_escape():
    with pytest.raises(ValueError, match="escapes"):
        ensure_write_path(Path("/tmp/outside-project"), project_root())


def test_evidence_serialization_is_round_trip_and_non_overwriting(tmp_path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    payload = {
        "truth_separation": {
            "reference_truth": "pinned source",
            "observation_truth": "raw OCR",
            "decision_truth": "AMBIGUOUS",
        },
        "japanese": "ハヤト",
    }
    first = write_json_new(tmp_path / "evidence.json", payload)
    second = write_json_new(tmp_path / "evidence.json", payload)
    assert first != second
    assert json.loads(first.read_text(encoding="utf-8")) == payload
    assert json.loads(second.read_text(encoding="utf-8")) == payload
