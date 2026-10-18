# MetaPrompt Process Reconstruction and Invariant Register

Status: **reconstructed process model for planning; not a runtime execution log**
Method: `MetaPrompt-Process-Reconstruction-Candidate-Suite`,
`reverse-engineering-a-process-by-invariant-detection`, ThinkLikeACIO, and SSAC

## 1. Evidence envelope

The envelope contains the target architecture, implementation status, sample
run, tests, taxonomy, governance/risk records, ECEGF gap analysis, lifecycle
standard, PM+Dev branch/release rules, and the supplied capability/process
skills. The envelope is version-bound to this repository state and must be
re-frozen before implementation milestones.

## 2. Candidate objects and relations

| Object | Role | Required relations |
|---|---|---|
| Capture | Immutable input | has PageObservation; addressed by hash |
| Page/Pocket/CardFace observation | Geometry and quality evidence | derived from Capture; contains zones |
| Template hypothesis / registry entry | Layout interpretation | constrains ZoneDefinition and classifier |
| Zone definition / localized zone observation | Semantic information area | linked to template, crop geometry, extractor attempts |
| Extractor attempt / observation | Raw and typed signal | produced from zone pixels; retains model and alternatives |
| Reference snapshot / printing | Catalogue truth candidate | source-mapped; may have rights/media restrictions |
| Candidate set / comparison | Competing identity hypotheses | joins observations to reference records |
| Discriminator plan | Next evidence action | targets missing information gain |
| Decision / review assertion | Qualified outcome | may abstain; human assertion supersedes without erasing evidence |
| Benchmark / calibration record | Truth and policy evidence | evaluates runs, thresholds, drift, and release gates |

## 3. Qualified invariant register

| ID | Invariant | Class | Consequence |
|---|---|---|---|
| I-01 | A source image is not a card identity | Semantic boundary | Identity requires evidence and candidate comparison |
| I-02 | Every material artifact is versioned, hashed, and provenance-bound | Evidence | Reproducible runs and challengeable decisions |
| I-03 | Template hypothesis is distinct from template fact | Epistemic | Classifier output must remain probabilistic/qualified |
| I-04 | A zone definition is distinct from a localized observation | Structural | Declared zones cannot be counted as detected zones |
| I-05 | Raw extractor output is never replaced by normalized values | Data integrity | Preserve alternatives, warnings, and failure modes |
| I-06 | Candidate ranking is not an identification decision | Decision | Fusion, contradiction, margin, and abstention are mandatory |
| I-07 | Missing permitted media is a data state, not silent retrieval permission | Governance | Media manifest and rights status gate comparison |
| I-08 | Human correction supersedes but does not erase machine evidence | Audit | Review is append-only and reversible |
| I-09 | Validation is not release authorization | Lifecycle | Promotion requires independent governance decision |
| I-10 | A benchmark must contain reviewed truth and split policy | Evaluation | Fixture success cannot substitute for general accuracy |
| I-11 | Template taxonomy, zone ontology, extractors, corpus fields, and evaluation co-evolve | Coupling | Contract changes require coordinated versioning |
| I-12 | Unknown/insufficient/ambiguous are valid outcomes | Safety | False confirmation is prioritized above coverage |

## 4. Variability register

- card product, face state, orientation, category, script, era, mechanic,
  region, exception, and printing vary independently enough to require
  hierarchical classification;
- layouts move, merge, split, or omit semantic zones;
- capture geometry, sleeve glare, skew, crop quality, and resolution vary;
- OCR, symbol, numeric, visual, and structured evidence can disagree;
- reference sources have field defects, missing images, language gaps, and
  rights restrictions;
- a run may proceed, partially complete, abstain, fail safely, or require
  human review.

## 5. Excluded circumstances

The reconstructed process does not authorize grading, condition assessment,
authenticity determination, pricing, silent web retrieval, image-rights
assumptions, automatic release promotion, or service decomposition without
measured need.

## 6. Reconstructed process model

1. **Govern:** bind intent, authority, scope, versions, and policies.
2. **Land:** hash and preserve capture and source snapshots.
3. **Ingest:** validate and map corpus records into canonical reference layers.
4. **Geometry:** locate pages, pockets, faces, orientation, quality, and
   reversible coordinates.
5. **Classify:** produce hierarchical template hypotheses with alternatives.
6. **Localize:** identify each semantic zone using priors, anchors, detectors,
   and candidate-conditioned alternatives.
7. **Extract:** run typed ensembles and preserve raw observations.
8. **Retrieve:** query reference data and produce candidates with provenance.
9. **Discriminate:** select the next evidence action by expected information
   gain and cost.
10. **Fuse:** compare typed evidence, record contradictions, and calibrate.
11. **Decide:** confirm only when gates pass; otherwise abstain or route review.
12. **Review:** capture human assertions as superseding, append-only evidence.
13. **Project:** emit inventory products without mutating truth layers.
14. **Evaluate:** benchmark, calibrate, detect drift, and replan.

## 7. Decision boundaries

| Boundary | Stop / escalate condition |
|---|---|
| Authority | Required approver, owner, or rights decision is absent |
| Evidence | Ground truth, media permission, or reproducibility metadata is missing |
| Contract | Schema or invariant changes without migration/version decision |
| Safety | Contradiction, low quality, or calibration failure would make confirmation unsafe |
| Lifecycle | Promotion or external exposure is requested without independent review |
| Scope | New product classes, services, or claims exceed the approved target |

## 8. Validation qualification

The model explains the motivating case (all-ambiguous sample), alternate cases
(different layouts and evidence families), and insufficient cases (no reference
image, no ground truth, or conflicting OCR). It is **qualified as a planning
model**. It is not proof that any unimplemented stage works. The Technical
Project Plan binds each invariant to a workstream, acceptance test, and
re-evaluation trigger.
