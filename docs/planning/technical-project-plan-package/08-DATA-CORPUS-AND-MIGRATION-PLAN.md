# Data, Corpus and Migration Plan

## Truth planes

1. Source truth: immutable bytes and source metadata.
2. Canonical reference truth: governed mappings into card/printing/variant
   objects without erasing source disagreement.
3. Observation truth: measured pixels, geometry and extractor alternatives.
4. Decision truth: versioned policy output, never reference fact.
5. Review truth: attributed action/supersession, not destructive correction.
6. Inventory projection: current effective view derived from the above.

## Core entities

`SourceRelease`, `SourceObject`, `MappingDecision`, `CanonicalCard`,
`Printing`, `Variant`, `MediaAsset`, `RightsDecision`, `Capture`, `CardFace`,
`TemplateHypothesis`, `ZoneObservation`, `ExtractionObservation`, `CandidateSet`,
`ComparisonEvidence`, `IdentificationDecision`, `ReviewAction`, `RunManifest`,
`InventoryProjection`, `BenchmarkItem` and `EvaluationReport`.

All durable IDs are stable, globally namespaced and immutable. Content objects
have SHA-256 digests. Relationships are explicit foreign keys/object IDs, not
display-name joins.

## Corpus ingestion

1. acquire under an explicit source/rights decision;
2. retain exact archive and license metadata;
3. verify digest and parse into staging;
4. map fields with a versioned mapping decision;
5. quarantine malformed, contradictory or unmappable records;
6. reconcile cardinality, referential integrity and checksums;
7. publish an immutable corpus version and index;
8. evaluate compatibility and mark dependent evidence stale where necessary.

Source defects remain visible. Null, unavailable, not-applicable, redacted and
unknown are different states.

## Schema/template/model migrations

| Change | Required action |
|---|---|
| additive optional field | forward/backward compatibility test |
| renamed/changed semantic field | new schema major version plus explicit transform |
| template/zone semantic change | registry migration, affected-family replay and stale marking |
| corpus identity merge/split | mapping decision, impact query, new projection; never rewrite evidence |
| model/extractor/policy change | new artifact ID and evaluation; prior runs remain reproducible |
| destructive storage change | backup, dry run, checksum, rollback rehearsal and human approval |

Migrations are expand → backfill → verify → switch readers → contract. Each
step is restartable and records counts/digests. Rollback restores reader
selection or projection; immutable source/evidence never rolls back by deletion.

## Retention and backup classes

- Source/canonical/evidence/review: immutable retained per approved rights and
  privacy schedule.
- Derived caches/indexes/crops: reproducible but retained when required for
  audit performance; safe to regenerate only after digest verification.
- Temporary uploads: promoted to immutable source or deleted under recorded
  policy; current pre-alpha adapter retains them.
- Secrets/tokens: never part of data packages or backups beyond secret manager.

## Data quality controls

Completeness, uniqueness, referential integrity, language/script validity,
identifier collision, printing/variant separation, rights state, image digest
duplication, mapping exceptions and source-to-canonical reconciliation are
reported for every corpus release.
