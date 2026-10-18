# CAP-009 — Typed Extraction Ensemble

Status: `REQUIRED / SPECIFIED_CANDIDATE`

Owner role: Observation Extraction Owner (`TO_BE_APPOINTED`)

## Outcome and scope

Produce replayable raw and typed observations from localized zones using
bounded, semantics-aware extractor ensembles. Candidate lexicons may rank
alternatives but may not overwrite raw outputs.

## Requirements and invariants

- Enforce I-05, I-11, and I-12.
- Support script-aware text, numeric fields, symbols, line/word geometry,
  artwork/full-face features, optical surface hypotheses, and specialized zones.
- Version model code, model data, preprocessing, lexicon, parameters, seed,
  budget, warnings, and failures.
- Preserve N-best raw outputs and explicit confusion transforms.
- Bound retries by evidence gain or budget.

## Contracts

Inputs: `LocalizedZoneObservation`, zone pixels/mask, extractor policy,
model/profile registry, optional candidate lexicon.

Outputs: `ExtractorAttempt`, `TextObservation`, `NumericObservation`,
`SymbolObservation`, `VisualFeatureObservation`, `ExtractionFailure`.

Providers conform to typed ports and declare supported zone types, quality
requirements, runtime isolation, and licensing/model-data status.

## Behavior, controls, and recovery

Select eligible providers/recipes; execute in isolated bounded workers where
needed; retain raw alternatives; parse typed values; apply validators; determine
whether more attempts add material evidence; persist every attempt. Provider
failure is contained and can fall back without hiding the failure.

## Acceptance evidence

- character/word/field accuracy, symbol F1, numeric exact match, N-best recall;
- measures by zone, language, template, quality, and provider profile;
- raw-to-normalized round-trip and confusion-transform tests;
- timeout/crash/license-unavailable/model-mismatch failure tests;
- repeated preprocessing variants are marked correlated downstream.

## Dependencies and increments

Upstream: CAP-001, CAP-002, CAP-007, CAP-008, CAP-014 fixtures. Downstream:
CAP-010, CAP-011, CAP-014.

Increments: attempt contract -> text/numeric -> symbols -> visual/specialized ->
ensemble stopping -> isolated provider/reliability benchmark.

## Boundary diagram

```mermaid
flowchart LR
    zone["Localized zone and pixels"] -->|"Attempts"| orchestrator["Extraction orchestrator"]
    policies[("Extractor profiles and model manifests")] -->|"Selects providers"| orchestrator
    orchestrator -->|"Runs bounded recipes"| providers["Typed extractor providers"]
    providers -->|"Raw alternatives"| orchestrator
    orchestrator -->|"Persists attempts"| evidence[("Observation store")]
    orchestrator -->|"Typed observations"| reasoning["Candidate reasoning"]
```

## Behavior diagram

```mermaid
flowchart LR
    start(["Localized zone ready"]) --> eligible["Select eligible providers and recipes"]
    eligible --> execute["Execute bounded attempt"]
    execute --> raw["Preserve raw N-best output and warnings"]
    raw --> parse["Parse typed candidates"]
    parse --> validate["Apply grammar and range validators"]
    validate --> enough{"Evidence or budget criterion met?"}
    enough -->|"No"| execute
    enough -->|"Yes"| persist(["Persist attempts and observations"])
```
