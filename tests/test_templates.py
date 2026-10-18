from pathlib import Path

from ptcg.template_registry import TemplateRegistry
from ptcg.localization import initialize_zone_observations


def test_template_inheritance_and_contrasting_family():
    root = Path(__file__).parents[1] / "templates"
    registry = TemplateRegistry(root)
    assert registry.validate() == []
    historical = registry.resolve("pokemon.ja.vs-owner.v1")
    modern = registry.resolve("pokemon.modern-standard.v1")
    assert historical["zones"]["collector_number"]["rect"] != modern["zones"]["collector_number"]["rect"]
    assert historical["series_hint"] == "VS"
    assert "card.base.v1" in historical["resolved_lineage"]


def test_compiled_registry_has_semantic_zone_coverage_and_stable_digest():
    root = Path(__file__).parents[1] / "templates"
    first = TemplateRegistry(root)
    second = TemplateRegistry(root)
    coverage = first.coverage()
    assert coverage["semantic_zone_count"] >= 19
    assert coverage["anchor_ids"] == [
        "artwork_frame",
        "body_frame",
        "footer_band",
        "header_band",
        "matchup_band",
    ]
    assert "catalogue" in coverage["semantic_families"]
    assert first.digest() == second.digest()
    assert all(
        zone["presence_states"]
        for zone in first.resolve("pokemon.ja.vs-owner.v1")["zones"].values()
    )
    assert all(
        zone["locator"]["anchor"] in first.resolve("pokemon.ja.vs-owner.v1")["anchors"]
        for zone in first.resolve("pokemon.ja.vs-owner.v1")["zones"].values()
    )


def test_every_declared_zone_gets_distinct_nonlocalized_observation():
    root = Path(__file__).parents[1] / "templates"
    template = TemplateRegistry(root).resolve("pokemon.ja.vs-owner.v1")
    observations = initialize_zone_observations(
        template,
        [[0, 0], [629, 0], [629, 879], [0, 879]],
        {"glare_fraction": 0.0, "laplacian_variance": 100.0},
    )
    assert set(observations) == set(template["zones"])
    assert all(item["presence_state"] == "NOT_LOCALIZED" for item in observations.values())
    assert all(item["localized"] is None for item in observations.values())
    assert observations["collector_number"]["semantic_family"] == "catalogue"
