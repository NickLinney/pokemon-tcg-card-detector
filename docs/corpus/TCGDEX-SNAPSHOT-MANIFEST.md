# TCGdex Snapshot Manifest

- upstream: `https://github.com/tcgdex/cards-database`
- tag: `v2.48.0`
- commit: `46e7d514d534d38257914a5ffee54c17849f72c3`
- local compiled database: `../.local/corpus/tcgdex-v2.48.0-r3.sqlite3`
- database SHA-256: `23243e4a7cdcbbb4c8c724af610a4335433f067edc8b94721d9c595399a79f0f`
- generated manifest SHA-256: `8579574cb433289a489f33998c12d68eb393a1546e28b8d56ea0c70f5ea71a33`
- imported records: 42,055
- import errors: 0
- SQLite integrity: `ok`
- upstream license-file SHA-256: `12e7dd2d018848b9997d0226c4632f01da86ec4bf6ebe0c8b19953d5e5eeb6ff`

Canonical reference IDs include the upstream source scope, for example
`tcgdex:data-asia:VS1-001`. This prevents collisions where the same upstream
card ID appears in different corpus scopes. The upstream `source_card_id` and
source-relative path remain separate fields.

Every record retains the raw TypeScript object and a source-payload hash.
Observed fields without first-class columns are counted in the manifest rather
than discarded (`boosters`: 1,391; `energyType`: 968).

The VS1 subset has no usable TCGdex reference images and contains materially
imperfect Japanese names, including mixed English species names. Those are
source facts and counterevidence, not values the detector may silently repair.
