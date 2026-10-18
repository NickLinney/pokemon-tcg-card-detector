import json
from pathlib import Path

from ptcg.cli import main
from ptcg.reviews import ReviewStore
from tests.test_reviews import build_review_run


def test_review_cli_lists_shows_decides_and_exports(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    database = tmp_path / "reviews.sqlite3"
    store = ReviewStore(database)
    review_id = store.index_run(build_review_run(tmp_path))[0]
    evidence_version = store.get(review_id)["evidence_version"]

    assert main(["review", "list", "--database", str(database)]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["items"][0]["review_id"] == review_id

    assert main(["review", "show", review_id, "--database", str(database)]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["evidence_version"] == evidence_version

    assert main(
        [
            "review",
            "decide",
            review_id,
            "--database",
            str(database),
            "--actor",
            "local:reviewer-1",
            "--authority-scope",
            "collection-1",
            "--action",
            "SELECT_CANDIDATE",
            "--reason",
            "Reviewed title and collector number.",
            "--evidence-version",
            evidence_version,
            "--reference-card-id",
            "tcgdex:sv1:001",
        ]
    ) == 0
    disposition = json.loads(capsys.readouterr().out)
    assert disposition["actor_id"] == "local:reviewer-1"

    output = tmp_path / "effective"
    assert main(
        [
            "inventory",
            "export",
            "collection-1",
            "--database",
            str(database),
            "--output",
            str(output),
        ]
    ) == 0
    exported = json.loads(capsys.readouterr().out)
    assert Path(exported["csv"]).is_file()
    assert Path(exported["jsonl"]).is_file()
    assert Path(exported["sqlite"]).is_file()
