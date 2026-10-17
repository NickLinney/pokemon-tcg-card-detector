# ADR-008: Robust evidence application architecture

Status: Proposed for Commissioner acceptance.

## Context

The first vertical slice proved that static template declarations and a small
number of OCR crops can preserve uncertainty, but it did not implement general
template classification or comprehensive per-card zone localization. Describing
that result as robust or meticulous would collapse a laboratory prototype into a
validated product claim.

## Decision

Adopt the target in
`docs/architecture/ROBUST-DETECTION-IDENTIFICATION-ARCHITECTURE.md`: a local-first
modular monolith with separate reference, perception, reasoning, review, and
evaluation planes; hierarchical top-k template inference; explicit zone
localization; typed extractor ensembles; dependency-aware evidence fusion; and
benchmark-gated automatic decisions.

## Consequences

- Template definitions and observed zone localizations become different object
  types.
- Card identity and printing identity receive separate decisions.
- Candidate-conditioned extraction is bounded by an information-gain planner.
- A ground-truth and calibration program is a product component, not optional
  test collateral.
- The current vertical slice remains historical evidence but is not the target
  architecture.
- No robustness claim is eligible before measured gates and independent review.
