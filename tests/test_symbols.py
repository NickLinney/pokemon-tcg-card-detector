import numpy as np

from ptcg.symbols import PrototypeSymbolProvider, UnsupportedSymbolProvider


def image(left: int, right: int):
    value = np.zeros((32, 32, 3), dtype=np.uint8)
    value[:, :16] = left
    value[:, 16:] = right
    return value


def test_unsupported_provider_retains_explicit_uncertainty():
    result = UnsupportedSymbolProvider().extract(
        image(0, 255), zone_id="set_symbol", template_id="pokemon.modern.v1"
    )
    assert result["state"] == "UNSUPPORTED"
    assert result["typed_value"] is None


def test_prototype_provider_is_stratum_bound_and_typed():
    provider = PrototypeSymbolProvider(
        prototypes={"set": {"sv": image(0, 255), "base": image(255, 0)}},
        approved_template_prefixes=("pokemon.modern",),
    )
    supported = provider.extract(
        image(0, 255), zone_id="set_symbol", template_id="pokemon.modern.v1"
    )
    assert supported["state"] == "SUCCEEDED"
    assert supported["typed_value"] == {"symbol_family": "set", "label": "sv"}
    outside = provider.extract(
        image(0, 255), zone_id="set_symbol", template_id="pokemon.historical.v1"
    )
    assert outside["state"] == "UNSUPPORTED"
    assert "outside approved" in outside["uncertainty"]
