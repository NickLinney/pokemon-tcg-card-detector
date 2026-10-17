# Template Taxonomy Register

| Template | Parent | Scope | Status |
|---|---|---|---|
| `card.base.v1` | none | Shared normalized semantic zones | Implemented |
| `pokemon.generic.v1` | `card.base.v1` | Generic Pokémon card | Implemented |
| `trainer.generic.v1` | `card.base.v1` | Generic Trainer card | Implemented |
| `energy.generic.v1` | `card.base.v1` | Generic Energy card | Implemented |
| `pokemon.ja.historical.v1` | `pokemon.generic.v1` | Historical Japanese yellow-border layout | Implemented |
| `pokemon.ja.vs-owner.v1` | `pokemon.ja.historical.v1` | 2001 VS owner-associated overlay | Implemented and exercised |
| `pokemon.modern-standard.v1` | `pokemon.generic.v1` | Modern standard layout contrast | Implemented, not fixture-calibrated |

Zones use normalized card-face coordinates and retain semantic meaning across
templates. Child templates override only the regions whose layout differs.
Template prediction is a hypothesis and is stored separately from observations.
