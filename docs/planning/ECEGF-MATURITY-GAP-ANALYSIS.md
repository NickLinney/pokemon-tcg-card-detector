# ECEGF Maturity Gap Analysis

Status: **provisional evaluation for planning; not an independent audit**
Framework: Enterprise Capability Evaluation and Governance Framework (ECEGF)
Scales: SICAF 1–5 (strategic design), RCMF 1–5 (operational reality)

## 1. Evaluation boundary

The subject is the capability to classify card templates, identify semantic
information zones, ingest reference data, analyze evidence, and produce a
qualified identity under the target architecture. Evidence is bounded to the
local repository, the commissioned nine-pocket sample, the pinned TCGdex
corpus, and the supplied governance resources. No independent evaluator,
approver, or reviewed ground-truth owner was supplied; therefore scores are
decision-support ratings with explicit confidence, not acceptance findings.

## 2. SICAF strategic design assessment

| Domain | Score | Rating | Evidence | Gap / impact |
|---|---:|---|---|---|
| Strategic Alignment | 3 | Defined | Target architecture and mandate are explicit | No authorized investment decision or outcome KPIs |
| Capability Definition | 2 | Emerging | Prototype and target delta are documented | General classifier and zone capability are not constructed; **High** |
| Operating Model Fit | 2 | Emerging | Governance ledger, risk register, branch rules exist | Owners, independent review cadence, and handoffs are not active; **High** |
| Process Architecture | 3 | Defined | Staged pipeline and target state machine are specified | Several target stages are design-only; **Moderate** |
| Information Architecture | 2 | Emerging | Truth layers and contracts are named | Printing/variant, zone observation, and benchmark schemas need implementation; **High** |
| Technology Enablement | 2 | Emerging | Local Python prototype, OCR, retrieval, serialization | Six-plane target topology is largely absent; **High** |
| Measures and Policy | 2 | Emerging | 12 tests and safety decisions exist | No reviewed benchmark, calibration, drift thresholds, or release scorecard; **High** |

SICAF average: **2.3 / 5 (Emerging)**.

## 3. RCMF operational assessment

| Domain | Score | Rating | Evidence | Gap / impact |
|---|---:|---|---|---|
| Process Execution | 2 | Repeatable | Local fixture run and staged serialization | One narrow fixture; no broad repeated campaign; **High** |
| Role Adoption | 1 | Ad Hoc | CIO/SSAC reasoning is recorded in this task | No active capability owner, reviewer, approver, or action owner; **High** |
| Control Effectiveness | 2 | Repeatable | Write guards, abstention, provenance, and no-override behavior | Independent control testing absent; **Moderate** |
| Data and Reporting | 2 | Repeatable | JSONL/CSV/SQLite evidence and sample report | No normalized full-zone report or benchmark dashboard; **High** |
| Technology Reliability | 2 | Repeatable | 12 tests pass; corpus integrity verified | Single local environment and limited failure injection; **Moderate** |
| Service Management | 1 | Ad Hoc | Unreleased local project | No incident, recovery, support, or operational cadence; **High** |
| Continuous Improvement | 2 | Repeatable | Ledger, risks, ADRs, and architecture delta exist | No closed-loop improvement register with owners and target dates; **Moderate** |

RCMF average: **1.7 / 5 (Repeatable)**.

## 4. Strategic-to-operational gap

| Gap ID | Strategic intent | Operational reality | Disposition | Priority |
|---|---|---|---|---|
| G-01 | General hierarchical template classification | Two-choice sample-specific predictor | Remediate | P0 |
| G-02 | Individual semantic-zone identification | Three zones localized at runtime; remaining zones declarative only | Remediate | P0 |
| G-03 | Canonical printing/variant-aware reference model | Pinned catalogue with rights/media and variant limitations | Remediate | P0 |
| G-04 | Evidence-qualified identification | Ambiguous safety outcome, no broad recall/precision benchmark | Remediate | P0 |
| G-05 | Human review and supersession | No review workbench | Remediate | P1 |
| G-06 | Calibrated policy and drift control | No benchmark-calibrated thresholds | Remediate | P0 |
| G-07 | Governed operating model | Records exist; accountable roles and recurring review do not | Mitigate then remediate | P1 |
| G-08 | Reproducible operational lifecycle | Local unreleased branch and no independent acceptance | Defer promotion; remediate controls | P1 |

## 5. Capability improvement register

| ID | Owner (to appoint) | Action | Success measure | Target gate |
|---|---|---|---|---|
| CIR-01 | Capability Owner | Approve template/zone ontology and registry contract | Versioned registry with review record | Before classifier work |
| CIR-02 | Data/Corpus Owner | Create reviewed fixtures and media-rights manifest | Ground-truth set with provenance and split policy | Before benchmark claims |
| CIR-03 | Perception Owner | Implement zone localization and geometry evidence | Per-zone localization metrics meet architecture thresholds | Before extraction expansion |
| CIR-04 | Reasoning Owner | Implement candidate/discriminator/fusion contracts | Contradiction and abstention cases pass fixture gates | Before confirmation claims |
| CIR-05 | Evaluation Owner | Build benchmark/calibration/drift harness | Reproducible scorecard and falsifier tests | Before lifecycle review |
| CIR-06 | Governance Lead | Establish independent review and closure cadence | Signed evaluation, action register, and closure basis | Before Alpha proposal |

## 6. ECEGF conclusion

The project is strategically **Emerging** and operationally **Repeatable at
prototype scope**. The decisive maturity gap is not the existence of OCR; it is
the absence of a verified, broad, contract-driven loop connecting template
classification, zone localization, reference ingestion, evidence fusion, and
calibrated review. The Technical Project Plan closes these gaps in dependency
order. Until the gap register is closed, “robust and meticulous” remains a
target descriptor, not a present-state claim.
