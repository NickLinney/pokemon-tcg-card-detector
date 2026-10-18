# Turn Context Into Project Context

Status: **candidate project context; awaiting authorized project baselining**
Derived with: `TurnContextIntoProject-Candidate-Suite`, Capability Factory,
MetaPrompt reconstruction, ECEGF, IFA, ThinkLikeACIO, and SSAC

## Human intent

Construct the application architecture and execution plan required to perform
specific, evidence-led card template classification, semantic information-zone
identification, reference ingestion, and analysis to an honest “robust and
meticulous” standard. Preserve uncertainty, provenance, and human correction;
do not turn a target architecture into a claim of completed capability.

## Charter

Build a local-first, evidence-led modular monolith that can ingest permitted
reference sources and photographed card captures, classify layout/template
types, identify and localize individual information zones, extract typed
observations, retrieve and compare candidates, abstain safely, support review,
and produce reproducible inventory evidence.

## Scope

In scope: the six architecture planes, canonical contracts, corpus and media
governance, geometry, template registry/classification, zone localization,
typed extractors, candidate reasoning, fusion/decision, review/inventory,
benchmark/calibration, reproducibility, and Pre-Alpha lifecycle controls.

Out of scope: grading, condition, authenticity, pricing, silent external
retrieval, uncontrolled cloud services, and production promotion before gates.

## Requirement register

| ID | Requirement | Provenance | Commitment |
|---|---|---|---|
| RQ-01 | Preserve immutable source, raw outputs, provenance, and hashes | Target architecture / invariant I-02 | Must |
| RQ-02 | Classify template hierarchy beyond a sample-specific two-choice predictor | User intent / ECEGF G-01 | Must |
| RQ-03 | Localize individual semantic zones, not merely declare them | User intent / ECEGF G-02 | Must |
| RQ-04 | Separate card identity from printing/variant assertions | Target architecture | Must |
| RQ-05 | Use typed extractor ensembles with raw alternatives | Target architecture / I-05 | Must |
| RQ-06 | Retrieve candidates, plan discriminators, fuse evidence, and abstain | Target architecture / I-06 | Must |
| RQ-07 | Provide review, supersession, and inventory projections | Target architecture / I-08 | Must |
| RQ-08 | Establish reviewed benchmarks, calibration, drift, and release gates | ECEGF / lifecycle standard | Must |
| RQ-09 | Preserve local-first deployment and PM+Dev branch/release governance | PM+Dev bundle | Must |
| RQ-10 | Do not claim robust/methodical capability before measurable gates pass | Architecture CIO decision | Must |
| RQ-11 | Expand scope only through explicit decision boundary | SSAC / ThinkLikeACIO | Must |
| RQ-12 | Resolve owners, approvers, rights, and independent review before promotion | ECEGF / lifecycle standard | Unresolved |

## Architecture candidate

The recommended candidate is H1 from the IFA report: a local-first modular
monolith with six planes and replaceable adapters. The target architecture is
the source of truth for component contracts; this project context is the
construction and acceptance interpretation.

## Workstream map

| WS | Workstream | Primary outputs |
|---|---|---|
| WS-0 | Governance and contracts | registry, schema versions, policy, run ledger |
| WS-1 | Corpus and media | snapshots, canonical printing model, rights manifest |
| WS-2 | Geometry and capture | page/pocket/card-face observations, quality, anchors |
| WS-3 | Taxonomy and registry | hierarchical labels, template inheritance, calibration data |
| WS-4 | Classification and zones | classifier, zone ontology, localization engine |
| WS-5 | Typed extraction | OCR, symbols, numerics, visual features, failure records |
| WS-6 | Candidate reasoning | retrieval, discriminator planner, comparison, contradiction model |
| WS-7 | Fusion and review | decision engine, review workbench, superseding assertions |
| WS-8 | Evaluation and operations | fixtures, benchmark, calibration, drift, reproducibility |
| WS-9 | Release and lifecycle | independent review, maturity evidence, promotion packet |

## Invariant and variability binding

Every workstream must trace its design and tests to the invariant register in
`MPPRR-PROCESS-RECONSTRUCTION-REPORT.md`; every variability dimension must have
either a fixture, a declared limitation, or an explicit unresolved state. A
declared zone without a localized observation is not counted as coverage.

## Acceptance model

Each milestone requires: reproducible command; versioned inputs; expected
artifacts; automated checks; failure/abstention cases; reviewer; and closure
basis. A passing unit test is necessary but cannot alone satisfy a lifecycle
promotion gate.

## Unresolved conditions

Capability owner, independent evaluator, approver, media-rights disposition,
reviewed ground-truth curator, benchmark scope, and target dates remain to be
appointed or confirmed. These are explicit decision boundaries, not silently
filled assumptions.
