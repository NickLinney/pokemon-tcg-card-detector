import tomllib
from pathlib import Path

from ptcg import __version__
from ptcg.cli import build_parser
from ptcg.version import CANONICAL_VERSION, LIFECYCLE, RELEASED


def test_version_surfaces_are_consistent():
    assert CANONICAL_VERSION == "0.2.0-pre-alpha.2"
    assert __version__ == "0.2.0.dev2"
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert project["project"]["version"] == __version__
    assert LIFECYCLE == "PRE_ALPHA"
    assert RELEASED is False


def test_cli_version_uses_canonical_identity(capsys):
    try:
        build_parser().parse_args(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    assert capsys.readouterr().out.strip() == "ptcg 0.2.0-pre-alpha.2"
