# Quality, Evaluation and Test Strategy

## Quality model

Correctness means preserving uncertainty and lineage, not merely producing a
name. Evaluation is stratified by capture condition, language, era, category,
template family, zone type, rarity/printing, corpus completeness and known/OOD
status. Aggregate accuracy may never hide a failing safety-critical stratum.

## Test layers

| Layer | Required coverage |
|---|---|
| Contract/unit | schemas, IDs, state transitions, parsers, validators, policies |
| Property/metamorphic | rotation, scale, brightness, compression, crop perturbation, ordering |
| Component | corpus, registry, geometry, classifier, localizer, extractor, retrieval, fusion |
| Integration | Python/CLI/API parity, store transactions, model/corpus/template compatibility |
| End-to-end | page → evidence → review → inventory on representative fixtures |
| Adversarial | glare, blur, sleeve, occlusion, counterfeit-like layouts, unknown templates, corrupt files |
| Non-functional | load, soak, resource limits, recovery, security and deterministic replay |

## Ground-truth protocol

Two independent annotations plus adjudication are required for identity,
printing and ambiguous zone polygons. Annotators cannot see production
predictions before first-pass labeling. Truth includes provenance, confidence,
adjudicator, timestamp and supersession. Splits are isolated by physical card,
capture session, printing and near-duplicate fingerprint to prevent leakage.

## Metric gates

| Capability | Metrics | Initial gate status |
|---|---|---|
| Card detection | precision/recall, pocket-order accuracy, corner error | `EvidenceRequired` |
| Template classification | hierarchical accuracy, top-k recall, ECE/Brier, OOD AUROC/recall | `EvidenceRequired` |
| Zone localization | presence-state accuracy, polygon IoU, edge error, crop completeness | `EvidenceRequired` |
| Extraction | CER/WER, exact match, symbol F1, N-best recall | `EvidenceRequired` |
| Retrieval | top-k recall, no-match recall, inclusion/exclusion explainability | `EvidenceRequired` |
| Decision | false-confirmation, correct abstention, calibration, coverage-risk | false-confirmation is the primary safety gate; numeric value requires owner acceptance |
| Operations | completion, retry, latency/resource percentiles, recovery | `EvidenceRequired` |

Threshold-setting procedure: run a sealed baseline; calculate uncertainty
intervals; identify risk tolerance and operational envelope; propose per-stratum
thresholds; obtain evaluation, product and risk acceptance; version the policy;
then rerun untouched holdout data. Test tuning data may not become holdout data.

## Regression policy

- Every escaped defect becomes a minimal immutable fixture plus affected-stratum
  test unless rights or privacy prohibit retention.
- Any false confirmation is severity 1 for the decision policy and blocks
  promotion until root cause and affected-range analysis complete.
- Changes to corpus, template, model, extractor or policy trigger the declared
  compatibility subset and stale-evidence marking.
- Flaky tests are quarantined only with owner, issue, expiry and non-bypass of a
  release gate.

## Current verification baseline

The repository currently has 16 passing tests covering templates, schemas,
parsers, conservative decisions, geometry, corpus integrity, write safety and
the Flask adapter. This is implementation evidence for the vertical slice, not
the target benchmark evidence.
