# Completeness Assessment and Charter

## Executive decision

The discovery estate before this package was **architecture-complete capability
planning**, not a fully specified production-delivery plan. It correctly
specified template classification, individual zone localization, typed
extraction, evidence fusion and abstention, but did not completely prescribe
runtime interfaces, container profiles, environments, CI/CD, operational
objectives, delivery accountabilities, security controls, estimates or the
evidence-bearing completion contract.

This package closes those planning omissions. The honest resulting statement is:

> A fully specified production-delivery **plan candidate** now exists. The
> implemented application remains an unreleased Pre-Alpha vertical slice.

## Charter

Construct a local-first Python application that ingests governed reference
corpora and card imagery; preserves immutable source evidence; detects card
faces; classifies card-template families with explicit uncertainty; localizes
each applicable semantic information zone; performs typed extraction; retrieves
and compares reference candidates; abstains when evidence is insufficient or
conflicting; supports attributed human review; and projects governed inventory
records without erasing observation or decision history.

The same application core must be callable:

1. as Python functions/classes;
2. through the `ptcg` command-line executable or `python -m ptcg`;
3. through a thin HTTP transport;
4. in a least-privilege Docker image and Docker Compose local deployment.

## Outcome measures

| Outcome | Required proof |
|---|---|
| No false certainty | false-confirmation ceiling, abstention and contradiction scorecards on sealed data |
| Template specificity | hierarchical top-k, calibration and unknown-family/OOD results by taxonomy stratum |
| Zone specificity | per-zone presence, polygon IoU/edge error and crop-completeness results |
| Reproducibility | source/config/code/corpus/template/model hashes and deterministic replay report |
| Traceability | source pixel → observation → candidate/comparison → decision → review/inventory lineage |
| Operability | recovery drill, resource envelope, SLO dashboard and incident exercise evidence |
| Governed release | signed QA, security, data, product and release-authority dispositions |

## Scope boundaries

In scope: upright and rotated binder/page captures, single-card crops, governed
reference ingestion, multilingual text/symbol/numeric extraction, printing-level
evidence where licensed reference data permits, review and inventory export.

Out of scope unless separately authorized: grading, authentication, monetary
valuation, marketplace trading, destructive collection updates, public
multi-tenant hosting, biometric processing, and unlicensed media acquisition.

## Current-state evidence

- Seven inherited YAML template definitions exist.
- Nineteen zones are declared for the VS-owner template, while the current
  runtime extracts title, HP and conditionally collector number.
- The present predictor is a narrow two-choice heuristic, not the target
  hierarchical classifier.
- A pinned local TCGdex corpus and evidence-preserving vertical slice exist.
- Sixteen local tests pass after introduction of the Flask adapter.
- No independent production, security, QA or release disposition exists.

## Gate G0 — plan authorization

Construction beyond reversible Pre-Alpha work starts only when accountable
humans confirm: capability owner, technical lead, data steward, security owner,
QA/evaluation owner and release authority; licensed corpus/media boundaries;
the target deployment context; and acceptable cost/latency constraints. Missing
answers are tracked as decisions, never silently assigned to the developer or
an agent.
