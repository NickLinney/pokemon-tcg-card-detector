# Delivery Plan, RACI, RAID and Human Gates

## Resourcing and estimate

The capability-sized estimate is 100–125 ideal engineer-weeks plus governed
annotation/review effort. With 4–5 appropriately skilled contributors, the
critical-path planning range is 28–36 calendar weeks; corpus/media licensing,
truth-set creation, GPU procurement or unavailable approvers can extend it.
This is a range for portfolio planning, not a commitment.

| Stage | Ideal engineer-weeks | Principal roles |
|---|---:|---|
| W0 governance/contracts | 6–8 | capability owner, tech lead, security/data |
| W1 truth/evidence | 12–15 | data, platform, evaluation, QA |
| W2 inputs/capture | 14–18 | data, CV, security |
| W3 taxonomy/classification/zones | 20–25 | CV/ML, domain, evaluation |
| W4 extraction/reasoning | 20–25 | ML, data, domain |
| W5 decision/review/inventory | 12–15 | app, domain, UX, evaluation |
| W6 operations/qualification | 16–19 | platform, security, QA, release |

## RACI

Roles are intentionally unassigned until humans accept them.

| Decision/deliverable | Capability Owner | Tech Lead | Data Steward | CV/ML | QA/Eval | Security/Platform | Release Authority |
|---|---|---|---|---|---|---|---|
| scope/taxonomy | A | C | C | R | C | I | I |
| canonical contracts | C | A/R | C | C | C | C | I |
| corpus/rights | C | C | A/R | I | C | C | I |
| models/templates/zones | A | C | C | R | C | I | I |
| thresholds/benchmark | C | C | C | C | A/R | C | I |
| security/deployment | I | C | I | I | C | A/R | C |
| lifecycle promotion | C | C | C | C | C | C | A/R |

No person may approve their own production readiness across all roles.

## Human decision requests

| ID | Decision | Needed by | Default if absent |
|---|---|---|---|
| DR-001 | name accountable roles | G0 | remain Pre-Alpha; reversible work only |
| DR-002 | approve taxonomy/zone semantics | before WP-021 | research continues; no classifier contract freeze |
| DR-003 | approve corpus/media rights | before media use/training | deny use |
| DR-004 | choose production deployment/data store | before WP-043 | local profile only |
| DR-005 | accept risk-based metric thresholds | before sealed gate | `EvidenceRequired`; no promotion |
| DR-006 | set retention/privacy policy | before shared operation | local restricted retention only |
| DR-007 | approve lifecycle/release | after WP-052 | not released/not promoted |

## RAID register

| ID/type | Item | Response/trigger | Owner role |
|---|---|---|---|
| R-01 | sparse historical/rare template truth | active sampling, uncertainty routing; trigger failing stratum | Capability/Eval |
| R-02 | printing variants collapse in sources | separate identity object and contradiction state | Data Steward |
| R-03 | correlated OCR/image evidence inflates confidence | evidence dependency graph and ablation | ML/Eval |
| R-04 | annotation leakage/disagreement | isolated splits, double annotation, adjudication | QA/Eval |
| R-05 | inference resource/latency exceeds envelope | profile, bounded planning, worker/GPU options | Platform |
| R-06 | licensed reference images unavailable | explicit unavailable state; do not weaken printing gate | Data/Security |
| R-07 | Flask sync endpoint is exposed | loopback only; replace with authenticated durable jobs | App/Security |
| A-01 | Python 3.12 and OCI runtime remain supported | revalidate quarterly and on upgrade | Tech Lead |
| I-01 | numeric gates unknown before baseline | execute threshold procedure | QA/Eval |
| D-01 | modular monolith and Flask edge adapter | revisit only with measured need | Tech Lead |

## Governance gates

G0 authorize plan; G1 contracts/truth; G2 corpus/rights/capture; G3 taxonomy/
zone/classifier; G4 extraction/retrieval/fusion; G5 decision/review; G6
operational qualification; G7 independent release. A gate requires actual
named dispositions and immutable evidence links. A missing approver is a
blocker for that gate, not permission to infer approval.

## Stop conditions

Stop affected work for authority conflict, destructive/unrecoverable operation,
unknown licensing, secret/personal-data exposure, evidence corruption,
uncontrolled false confirmation, incompatible migration without rollback, or a
required human choice whose alternatives materially change architecture.
