# Product Requirements and Scope

## Actors and primary journeys

| Actor | Journey | Required result |
|---|---|---|
| Operator | ingest a pinned reference release | immutable manifest, mapping report, quarantine and verified searchable corpus |
| Collector/operator | analyze a binder page or card | ordered observations, evidence packages and qualified inventory proposals |
| Reviewer | resolve ambiguous/conflicting results | attributed append-only review action and effective-state projection |
| Data steward | correct mappings/truth | versioned adjudication with impact and replay plan |
| Evaluator | run sealed benchmark | stratified metrics, calibration, regression and nonconformance report |
| Operator/SRE | deploy, monitor, recover | known version, health/readiness, audit trail and tested restoration |

## Functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| FR-001 | Accept single-card and multi-card page images without mutating originals | input hash, immutable object, rejection fixtures |
| FR-002 | Detect cards, orientation and reversible source geometry | per-stratum geometry scorecard and source-coordinate replay |
| FR-003 | Classify category → era/layout → language/region → family → subtype with top-k uncertainty and OOD escape | hierarchy confusion matrix, top-k/OOD/calibration report |
| FR-004 | Resolve a versioned template registry with inheritance, predicates, anchors and compatibility rules | registry validation, cycle/overlap/negative fixtures |
| FR-005 | Localize every applicable semantic zone independently of declaration | per-zone observation or explicit absence/unlocalized state |
| FR-006 | Extract typed text, symbols, numbers, repeated structures and printing marks while retaining raw/N-best alternatives | typed validators, replay fixtures and N-best recall |
| FR-007 | Ingest canonical cards, printings, variants, mappings and governed media rights | referential checks, rights manifest and source reconciliation |
| FR-008 | Retrieve high-recall candidates and select bounded information-gain discriminators | top-k/no-match recall and planner termination evidence |
| FR-009 | Compare independent evidence, model dependencies/contradictions and produce calibrated abstaining decisions | false-confirmation, calibration and contradiction suites |
| FR-010 | Support attributed review, supersession and inventory projections | append-only history and effective-state tests |
| FR-011 | Resume safe work after interruption without duplicate/corrupt output | idempotency, checkpoint and failure-injection tests |
| FR-012 | Expose equivalent core behavior to Python, CLI and HTTP adapters | adapter contract and parity tests |

## Non-functional requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR-001 Safety | never confirm identity/printing without policy-sufficient independent evidence | sealed false-confirmation ceiling |
| NFR-002 Provenance | every derived object carries source, code, config, schema and dependency version IDs | lineage completeness query |
| NFR-003 Reproducibility | replay with the same manifest is deterministic within declared tolerance | cross-run digest/delta report |
| NFR-004 Security | least privilege, non-root containers, bounded uploads, no implicit model downloads | threat-control tests and image scan |
| NFR-005 Privacy | local-first processing, explicit retention and no image egress by default | configuration and network-egress test |
| NFR-006 Operability | observable state, structured logs, health/readiness, recovery and capacity envelopes | runbook exercises and SLO dashboard |
| NFR-007 Maintainability | modular monolith, typed/versioned contracts, architecture tests | dependency and compatibility checks |
| NFR-008 Portability | Python 3.12+, OCI image and Compose local profile | build/smoke matrix |
| NFR-009 Accessibility | review UI, if built, supports keyboard and non-color state cues | accessibility test record |
| NFR-010 Cost control | bounded rounds, candidate limits, resource/time budgets | load/cost report by workload class |

## Semantic-zone minimum ontology

Identity/header, classification, artwork, rules/body, combat/statistics,
footer/printing, machine-readable and condition/quality families must cover the
zone list in architecture section 9. Repeated attacks/abilities are arrays of
instances. A zone record includes applicability, presence state, polygon,
confidence, locator evidence, crop digest, transformation, alternatives and
failure reason.

## Constraint register

- No public network dependency is allowed in the default analysis path.
- Media use is denied unless the rights state explicitly permits the operation.
- Current synchronous HTTP analysis is a local Pre-Alpha adapter; production
  design uses durable asynchronous jobs.
- GPU acceleration is optional; CPU correctness must remain available.
- The architecture does not guarantee every historical or promotional layout;
  unsupported families must route to OOD/review, not forced classification.
