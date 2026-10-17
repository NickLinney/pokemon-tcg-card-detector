from pathlib import Path

from ptcg.template_registry import TemplateRegistry


def test_template_inheritance_and_contrasting_family():
    root = Path(__file__).parents[1] / "templates"
    registry = TemplateRegistry(root)
    assert registry.validate() == []
    historical = registry.resolve("pokemon.ja.vs-owner.v1")
    modern = registry.resolve("pokemon.modern-standard.v1")
    assert historical["zones"]["collector_number"]["rect"] != modern["zones"]["collector_number"]["rect"]
    assert historical["series_hint"] == "VS"
    assert "card.base.v1" in historical["resolved_lineage"]
