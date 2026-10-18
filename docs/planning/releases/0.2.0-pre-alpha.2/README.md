# Pokémon TCG Detector — `0.2.0-pre-alpha.2` Release-Plan Package

- **Plan-package version:** `0.2.0-pre-alpha.2`
- **Target product version:** `0.2.0-pre-alpha.2`
- **Status:** planning candidate; implementation and release have not occurred
- **Baseline:** Git commit `6f4003150d7703f87ee07dd23a810afd062b033f`
- **Prepared:** 2026-10-18

This package extends the product-development baseline with a governed Software
Release Lifecycle Development Plan derived from the container UAT and the target
robust detection/identification architecture.

The target uses the project-specific convention confirmed by the Commissioner:
the `0.2.0` core communicates a pre-1.0 minor capability increment while
`pre-alpha.2` preserves the experimental lifecycle classification. This release
does not imply or require promotion to Alpha. The inherited generic
`0.0.0-pre-alpha.N` text is recorded as a governance discrepancy to be resolved
through an explicit repository-level adaptation before release preparation.

## Package index

- [`SOFTWARE-RELEASE-LIFECYCLE-DEVELOPMENT-PLAN.md`](SOFTWARE-RELEASE-LIFECYCLE-DEVELOPMENT-PLAN.md)
  — executive product release plan, lifecycle, architecture increment, gates,
  delivery waves, release mechanics, rollback and completion contract.
- [`RELEASE-BACKLOG-AND-TRACEABILITY.md`](RELEASE-BACKLOG-AND-TRACEABILITY.md)
  — actors, use cases, user stories, acceptance criteria, CAP/WP/UAT mappings
  and dependency order.
- [`EVIDENCE-AND-STRATEGY-EXECUTION-RECORD.md`](EVIDENCE-AND-STRATEGY-EXECUTION-RECORD.md)
  — source qualification, selected Skills, ThinkLikeACIO decisions, SSAC
  dispositions, discrepancies and nonclaims.
- [`release-plan.json`](release-plan.json) — machine-readable release identity,
  scope, gates and backlog summary.
- [`PACKAGE-MANIFEST.sha256`](PACKAGE-MANIFEST.sha256) — integrity manifest for
  every package member other than the manifest itself.
- [`diagrams/`](diagrams/) — editable Mermaid sources for the value stream and
  lifecycle state model.
- [`evidence/`](evidence/) — SSAC event inputs and deterministic advisory
  results, including the bounded version-correction replan.

## Product outcome

The release is intended to transform the accepted local CSV-proposal
demonstration into a reviewable, asynchronous, context-aware local Pre-Alpha
workflow. It adds governed artifact retrieval and attributable human review so
an ambiguous proposal can become an effective inventory assertion without
misrepresenting automatic identification accuracy.

It does **not** claim robust automatic card or printing identification. The
release must keep automatic confirmation disabled until CAP-014 calibration and
false-confirmation gates are independently accepted.
