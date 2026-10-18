# Requirement and Traceability Matrix

| Requirement | Source | Owning capabilities | Acceptance evidence |
|---|---|---|---|
| Preserve immutable evidence and provenance | I-02, target sections 4/5/17 | CAP-001, CAP-002, CAP-015 | hash, manifest, replay, atomicity and tamper tests |
| Canonicalize corpus without erasing source defects | target section 6 | CAP-003 | mapping register, quarantine, referential and checksum reports |
| Govern media rights and fingerprints | I-07, target sections 4/6 | CAP-004 | rights manifest, unavailable states, fingerprint fixtures |
| Recover reversible capture geometry and quality | target sections 3/16/18 | CAP-005 | precision/recall, corner error, crop completeness, quality fixtures |
| Classify template hierarchy with unknown escape | I-03, G-01, target section 7 | CAP-006 | top-k, calibration, hierarchy confusion, OOD recall |
| Define versioned template and zone semantics | I-04/I-11, target sections 8/9 | CAP-007 | registry validation, fixtures, migration/compatibility report |
| Localize every applicable information zone | G-02, target section 10 | CAP-008 | per-zone IoU/edge/presence/crop-completeness metrics |
| Preserve raw typed extractor alternatives | I-05, target section 11 | CAP-009 | replay and N-best recall; warning/failure provenance |
| Maximize candidate recall and request information | I-06, target section 12 | CAP-010 | top-k/no-match recall and bounded planner termination |
| Model evidence dependencies and contradictions | I-06/I-11, target section 13 | CAP-011 | dependency graph, comparator fixtures, contradiction tests |
| Abstain unless identity and printing gates pass | I-01/I-12, target section 13 | CAP-012 | false-confirmation, unresolved, calibration, separation tests |
| Preserve attributed review and inventory projection | I-08, target section 14 | CAP-013 | append-only supersession and effective-state projection tests |
| Use reviewed truth, split policy, calibration, drift | I-09/I-10, target section 18 | CAP-014 | sealed benchmark, leakage checks, scorecard and drift report |
| Operate securely, recoverably, and reproducibly | target sections 16/17 | CAP-015 | threat controls, failure injection, recovery and deterministic replay |
| Require independent lifecycle decision | I-09, lifecycle standard | CAP-001, CAP-014, CAP-015 | actual role dispositions and release record |

## Cross-capability verification suites

| Suite | Capabilities | Proves |
|---|---|---|
| CV-01 Source-to-observation lineage | CAP-001/002/005/008/009 | every derived result maps to exact pixels/configuration |
| CV-02 Reference-to-candidate lineage | CAP-003/004/010/011 | candidate inclusion and comparison are reproducible |
| CV-03 Hypothesis-to-decision safety | CAP-006/008/009/010/011/012 | uncertainty and dependencies survive to abstention |
| CV-04 Review-to-inventory lineage | CAP-002/012/013 | supersession changes effective state without history loss |
| CV-05 Benchmark-to-policy lineage | CAP-001/012/014 | thresholds bind to versioned evidence and strata |
| CV-06 Recovery and reproducibility | CAP-001/002/015 | interrupted/failed runs resume without corrupting evidence |
