# Capability Candidate Register

## Classification method

A candidate is `REQUIRED` when removing it breaks at least one target
architecture truth condition, invariant, production-readiness obligation, or
end-to-end acceptance path. Candidates are separate from modules, files, roles,
and implementations.

| ID | Capability candidate | Disposition | Primary invariants | Architecture plane |
|---|---|---|---|---|
| CAP-001 | Governance, Contract Registry, and Run Orchestration | REQUIRED | I-02, I-09, I-11 | Control / governance |
| CAP-002 | Immutable Artifact, Evidence, and Provenance Management | REQUIRED | I-01, I-02, I-05, I-08 | Cross-plane evidence |
| CAP-003 | Reference Corpus Ingestion and Canonicalization | REQUIRED | I-01, I-02, I-07, I-11 | Reference / corpus |
| CAP-004 | Governed Reference Media and Fingerprinting | REQUIRED | I-01, I-07 | Reference / corpus |
| CAP-005 | Capture Geometry, Normalization, and Quality Assessment | REQUIRED | I-01, I-02, I-12 | Perception |
| CAP-006 | Hierarchical Template Classification | REQUIRED | I-03, I-11, I-12 | Perception / interpretation |
| CAP-007 | Template Registry and Semantic Zone Ontology | REQUIRED | I-03, I-04, I-11 | Control / interpretation |
| CAP-008 | Semantic Zone Localization | REQUIRED | I-04, I-11, I-12 | Perception / interpretation |
| CAP-009 | Typed Extraction Ensemble | REQUIRED | I-05, I-11, I-12 | Perception / interpretation |
| CAP-010 | Candidate Retrieval and Active Discrimination | REQUIRED | I-01, I-06, I-11, I-12 | Candidate reasoning |
| CAP-011 | Typed Evidence Comparison and Dependency-Aware Fusion | REQUIRED | I-05, I-06, I-11 | Candidate reasoning |
| CAP-012 | Abstaining Identity and Printing Decision | REQUIRED | I-01, I-06, I-12 | Decision |
| CAP-013 | Human Review, Supersession, and Inventory Projection | REQUIRED | I-08, I-09, I-12 | Review / inventory |
| CAP-014 | Ground Truth, Evaluation, Calibration, and Drift Control | REQUIRED | I-09, I-10, I-11 | Evaluation / assurance |
| CAP-015 | Security, Reliability, Recovery, and Reproducible Operations | REQUIRED | I-02, I-07, I-09 | Operations / assurance |

## Candidate boundaries

- CAP-006 proposes template hypotheses; CAP-007 defines template/zone meaning;
  CAP-008 observes zones. These identities must not collapse.
- CAP-009 emits observations; CAP-010 emits candidate hypotheses; CAP-011 emits
  comparisons and fused evidence; CAP-012 alone emits machine decisions.
- CAP-013 emits attributable human assertions and inventory projections without
  rewriting evidence.
- CAP-014 supplies measurement and calibrated policy evidence; it does not
  authorize release.
- CAP-015 provides operational controls; it does not convert local validation
  into production acceptance.

## Excluded/deferred candidates

| Candidate | Disposition | Reason |
|---|---|---|
| Vector retrieval platform | DEFER | Conventional structured/FTS retrieval must be benchmarked first |
| Distributed microservices | DEFER | No measured concurrency or isolation need |
| Autonomous media crawler | EXCLUDE | Rights and silent-retrieval conflict |
| Grading / condition | EXCLUDE | Outside declared product scope |
| Authenticity determination | EXCLUDE | Unsupported claim and evidence model |
| Pricing / valuation | EXCLUDE | Separate market-data capability and governance |

## Specification index

- [`CAP-001-GOVERNANCE-CONTRACTS-RUN-ORCHESTRATION.md`](specifications/CAP-001-GOVERNANCE-CONTRACTS-RUN-ORCHESTRATION.md)
- [`CAP-002-IMMUTABLE-ARTIFACT-EVIDENCE-PROVENANCE.md`](specifications/CAP-002-IMMUTABLE-ARTIFACT-EVIDENCE-PROVENANCE.md)
- [`CAP-003-REFERENCE-CORPUS-INGESTION-CANONICALIZATION.md`](specifications/CAP-003-REFERENCE-CORPUS-INGESTION-CANONICALIZATION.md)
- [`CAP-004-GOVERNED-REFERENCE-MEDIA-FINGERPRINTING.md`](specifications/CAP-004-GOVERNED-REFERENCE-MEDIA-FINGERPRINTING.md)
- [`CAP-005-CAPTURE-GEOMETRY-NORMALIZATION-QUALITY.md`](specifications/CAP-005-CAPTURE-GEOMETRY-NORMALIZATION-QUALITY.md)
- [`CAP-006-HIERARCHICAL-TEMPLATE-CLASSIFICATION.md`](specifications/CAP-006-HIERARCHICAL-TEMPLATE-CLASSIFICATION.md)
- [`CAP-007-TEMPLATE-REGISTRY-SEMANTIC-ZONE-ONTOLOGY.md`](specifications/CAP-007-TEMPLATE-REGISTRY-SEMANTIC-ZONE-ONTOLOGY.md)
- [`CAP-008-SEMANTIC-ZONE-LOCALIZATION.md`](specifications/CAP-008-SEMANTIC-ZONE-LOCALIZATION.md)
- [`CAP-009-TYPED-EXTRACTION-ENSEMBLE.md`](specifications/CAP-009-TYPED-EXTRACTION-ENSEMBLE.md)
- [`CAP-010-CANDIDATE-RETRIEVAL-ACTIVE-DISCRIMINATION.md`](specifications/CAP-010-CANDIDATE-RETRIEVAL-ACTIVE-DISCRIMINATION.md)
- [`CAP-011-EVIDENCE-COMPARISON-DEPENDENCY-FUSION.md`](specifications/CAP-011-EVIDENCE-COMPARISON-DEPENDENCY-FUSION.md)
- [`CAP-012-ABSTAINING-IDENTITY-PRINTING-DECISION.md`](specifications/CAP-012-ABSTAINING-IDENTITY-PRINTING-DECISION.md)
- [`CAP-013-HUMAN-REVIEW-SUPERSESSION-INVENTORY.md`](specifications/CAP-013-HUMAN-REVIEW-SUPERSESSION-INVENTORY.md)
- [`CAP-014-GROUND-TRUTH-EVALUATION-CALIBRATION-DRIFT.md`](specifications/CAP-014-GROUND-TRUTH-EVALUATION-CALIBRATION-DRIFT.md)
- [`CAP-015-SECURITY-RELIABILITY-RECOVERY-OPERATIONS.md`](specifications/CAP-015-SECURITY-RELIABILITY-RECOVERY-OPERATIONS.md)
