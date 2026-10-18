# Technical Project Plan: Robust Detection and Identification Architecture

Status: **Pre-Alpha construction plan; not a release authorization**
Plan owner: **to be appointed**
Architecture baseline: [`ROBUST-DETECTION-IDENTIFICATION-ARCHITECTURE.md`](../architecture/ROBUST-DETECTION-IDENTIFICATION-ARCHITECTURE.md)
Project context: [`TURN-CONTEXT-INTO-PROJECT-CONTEXT.md`](TURN-CONTEXT-INTO-PROJECT-CONTEXT.md)

## 1. Executive intent

Construct the target architecture faithfully enough that the application can
make a qualified statement about card template type, individual information
zones, catalogue identity, language/set/number, and observable printing
variants—while retaining the evidence needed to reproduce, challenge,
supersede, or improve every result. “Robust and meticulous” becomes an earned
claim only after the benchmark and governance gates in this plan pass.

## 2. Current baseline and constraints

- Branch: `feature/pre-alpha-1-vertical-slice`.
- Baseline commits: `4b66494`, `59a0e14`, `906b204`, target architecture
  commit `f0281c8`.
- Current evidence: 12 tests pass; 9/9 sample cards segmented; all 9 sample
  decisions are `AMBIGUOUS`; no sample reference-image comparisons.
- Current limitation: seven representative templates and nineteen declared
  zones exist, but runtime localizes/extracts only title, HP, and collector
  number; the classifier is sample-specific.
- Lifecycle: unreleased Pre-Alpha 1. No independent QA, security, licensing,
  or release acceptance has occurred.
- Constraints: local-first operation, pinned corpus, explicit media rights,
  append-only evidence, no silent retrieval, and no direct `main` changes.

## 3. Capability Factory execution profile

This plan is the composite strategy produced by the Capability Factory pattern.
The stages are retained so later work can be audited rather than treated as a
black-box plan:

| Factory stage | Project realization |
|---|---|
| S01 Governance and intent | Human intent, authority boundary, SSAC `ADMIT_QUALIFIED` |
| S02 Evidence/context freeze | Repository baseline, hashes, sample, skills, lifecycle sources |
| S03 Independent projections | IFA hypotheses, ECEGF ratings, process invariants |
| S04 Comparison | H0/H1/H2/H3 decision packet and maturity gap |
| S05 Constructive synthesis | This plan and its dependency graph |
| S06 Capability owner selection | Owner fields remain unresolved; appointment is a gate |
| S07 Dependency compilation | WS-0 through WS-9 and critical path below |
| S08 Pattern/candidate discovery | Modular monolith, six planes, contract-first construction |
| S09 Nested fulfillment binding | Each workstream binds to architecture contracts and invariants |
| S10 Package materialization | Markdown reports, project context, plan, and traceability |
| S11 Validation/audit | Link checks, status checks, no-claim checks, and repository review |
| S12 Zip release | Not performed; repository artifacts are the current deliverable |
| S13 Publication readiness | Deferred pending independent review and lifecycle decision |
| S14 Cybernetic return | ECEGF improvement register and milestone re-planning |

## 4. Work breakdown and deliverables

### WS-0 — Governance and contract foundation (P0)

Deliver: versioned object schemas; registry manifest; run state machine;
authority/role matrix; policy and evidence ledger; migration rules.

Acceptance: every persisted object has stable ID, schema version, producer,
time, provenance, and content hash where applicable; write boundaries and
truth-layer separation are tested.

### WS-1 — Corpus, printing, variants, and media (P0)

Deliver: snapshot adapters; normalized series/set/card/printing/variant model;
field mapping decisions; media fingerprint/rights manifest; corpus validation
findings.

Acceptance: raw source is reproducible; mapping defects remain visible; a
printing cannot be inferred from card identity alone; prohibited media is
represented as unavailable rather than fetched.

### WS-2 — Capture geometry and quality (P0)

Deliver: page/pocket/card-face observations; orientation; corner/edge geometry;
quality and glare signals; reversible crop and mask records; anchor markers.

Acceptance: reviewed fixtures measure segmentation, localization, orientation,
and quality by template family; every crop maps back to source pixels.

### WS-3 — Taxonomy and template registry (P0)

Deliver: hierarchical labels for product, face state, orientation, category,
script, era, mechanic, region, exception, and printing; versioned inherited
templates; representative and adversarial fixtures.

Acceptance: classifier outputs alternatives and calibrated probabilities;
registry validation catches missing/overlapping/incompatible zones; taxonomy
changes are versioned and migrated.

### WS-4 — Template classification and zone localization (P0)

Deliver: feature extraction; hierarchical classifier; semantic zone ontology;
localization engine using template priors, anchors, detector proposals, and
candidate-conditioned alternatives; per-zone evidence records.

Acceptance: every claimed zone has a localized observation or explicit
`UNLOCALIZED`; metrics cover per-template/per-zone precision, recall, IoU,
orientation, and abstention; declared zones are never counted as detected.

### WS-5 — Typed extraction ensemble (P1)

Deliver: OCR, numeric, symbol, language, mechanics, set/number, and visual
feature extractors; preprocessing recipes; raw alternatives and warning/failure
records; model/data manifests.

Acceptance: extractor attempts are replayable; typed parsers preserve raw
values; disagreement produces contradiction/missing-discriminator evidence.

### WS-6 — Retrieval and active discrimination (P1)

Deliver: candidate query plan; structured/text retrieval; candidate set and
assessment; information-gain discriminator planner; typed comparisons.

Acceptance: retrieval metrics are measured on reviewed truth; planner chooses
the next affordable evidence action; missing reference media and weak source
fields reduce qualification rather than disappear.

### WS-7 — Fusion, abstention, review, inventory (P1)

Deliver: dependency-aware evidence fusion; confidence calibration; contradiction
ledger; abstaining decision engine; review workbench; superseding assertions;
JSONL/CSV/SQLite projections.

Acceptance: false-confirmation tests pass; ambiguous/insufficient/review states
are stable; human corrections append evidence and do not overwrite machine
history.

### WS-8 — Evaluation and operations (P0)

Deliver: fixture registry, train/tune/test split policy, benchmark harness,
calibration registry, regression/drift reports, reproducibility manifest,
failure-injection suite, and local runbook.

Acceptance: scorecard reports per-class, per-zone, and end-to-end metrics;
threshold changes are versioned; a falsifier can block promotion; two clean
replays produce equivalent evidence products.

### WS-9 — Independent review and lifecycle (P0)

Deliver: ECEGF evaluation packet; security/licensing/QA review; risk and
improvement closure; release candidate decision record.

Acceptance: named capability owner, evaluator, approver, and action owners;
independent review complete; lifecycle decision explicitly records promotion,
deferral, or continued Pre-Alpha.

## 5. Dependency graph and milestones

| Milestone | Dependency | Exit evidence |
|---|---|---|
| M0 Baseline freeze | Existing repository | Hash/register, branch, scope, owner appointment request |
| M1 Contract foundation | M0 | Schemas, registry, run state, governance tests |
| M2 Truth fixtures | M1 | Reviewed fixtures, rights manifest, split policy |
| M3 Corpus/geometry | M2 | Canonical reference model and reversible geometry metrics |
| M4 Taxonomy/classifier | M3 | Hierarchical classifier and calibration report |
| M5 Zone coverage | M4 | Per-zone localization metrics and abstention cases |
| M6 Typed evidence | M5 | Replayable extractor attempts and typed observations |
| M7 Reasoning/review | M6 | Candidate, discriminator, fusion, review, inventory evidence |
| M8 Benchmark gate | M7 | End-to-end scorecard, calibration, drift and falsifier results |
| M9 Lifecycle decision | M8 | Independent ECEGF review and promotion/defer record |

Critical path: `M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M8 -> M9`.

## 6. Backlog and traceability

| ID | Work item | Trace |
|---|---|---|
| TP-001 | Define object schemas and migrations | RQ-01, I-02, I-11 |
| TP-002 | Build reviewed fixture and media protocol | RQ-08, I-10 |
| TP-003 | Implement canonical printing/variant ingestion | RQ-04, G-03 |
| TP-004 | Implement geometry/anchor evidence | RQ-01, WS-2 |
| TP-005 | Expand taxonomy and registry | RQ-02, I-03 |
| TP-006 | Implement hierarchical classifier | RQ-02, G-01 |
| TP-007 | Implement all-zone localization | RQ-03, I-04, G-02 |
| TP-008 | Expand typed extractor ensemble | RQ-05, I-05 |
| TP-009 | Implement retrieval/discriminator/fusion | RQ-06, I-06 |
| TP-010 | Implement review and supersession | RQ-07, I-08 |
| TP-011 | Build benchmark/calibration/drift gates | RQ-08, I-10 |
| TP-012 | Conduct independent review and lifecycle decision | RQ-10, RQ-12, I-09 |

## 7. Definition of done for the architecture claim

The phrase “robust and meticulous” may be used for the implemented detector
only when all of the following are true:

- template classification is measured across the approved taxonomy, including
  abstention and out-of-distribution cases;
- each required semantic zone is localized and scored separately;
- corpus identity, printing/variant assertions, media rights, and provenance
  are explicit;
- typed extraction, candidate reasoning, contradiction handling, and human
  review are replayable and append-only;
- end-to-end metrics, calibration, drift, and false-confirmation rates pass
  versioned gates on reviewed truth;
- independent evaluator and approver decisions are recorded;
- lifecycle and release controls are satisfied.

## 8. Branch, release, and lifecycle execution

Continue development on feature branches. Integrate through `dev`, validate on
`test`, use `staging` only as the controlled UAT surface, and create a scoped
release branch such as `release/pre-alpha-2-robust-architecture` when the
milestone is ready. `main` changes only through an authorized release event;
the release branch is retained. No Alpha or general-support statement is
permitted until WS-9 closes.

## 9. Risks, decisions, and stop conditions

High risks are ground-truth scarcity, media rights, taxonomy breadth, OCR and
zone ambiguity, calibration, and absent independent roles. Stop or escalate
when an authority/rights decision is missing, a contract invariant changes,
benchmark truth is insufficient, or a proposed claim exceeds evidence. Safe
continuation consists of schema/fixture work, reversible experiments, and
documentation; it does not include silently relaxing gates.

## 10. Handoff and review cadence

At every milestone, publish the artifact register, evidence hashes, metrics,
unresolved states, and next-owner request. The plan should be reviewed at each
ECEGF Evaluate -> Report -> Plan -> Improve -> Review cycle. The next transition
is M0 baseline freeze followed by appointment of the capability owner,
independent evaluator, approver, and reviewed-fixture curator.
