# Implementation Status

The target architecture is defined in
`docs/architecture/ROBUST-DETECTION-IDENTIFICATION-ARCHITECTURE.md`. The statuses
below describe the current vertical slice only and must not be read as a claim
that the target architecture has been constructed.

## Implemented and verified

- governed repository bootstrap and bounded write guard;
- pinned TCGdex ingestion, raw-payload preservation, collision-safe IDs, and
  integrity verification;
- 3x3 segmentation, normalization, reversible geometry, and quality signals;
- template inheritance and registry validation;
- Japanese/English OCR, raw alternatives, HP and collector-number parsing;
- local candidate retrieval, scoring, discriminator planning, and conservative
  decision states;
- synthetic pHash/ORB comparison with a printing-identity nonclaim;
- evidence, page-summary, and inventory serialization;
- schema definitions and 12 passing unit/integration tests;
- commissioned nine-pocket sample run.

## Partial or evidence-limited

- sample identification: nine candidate lists produced, but all nine decisions
  correctly remain `AMBIGUOUS`;
- image comparison: implemented and tested synthetically, but not exercised on
  the sample because VS1 reference images are unavailable in the pinned corpus;
- template coverage: representative hierarchy exists, not broad historical
  calibration;
- OCR calibration: usable on several title/HP zones, not reliable across all
  nine low-resolution sleeved cards.
- template classification: the sample-specific predictor ranks only VS-owner
  and modern-standard; it is not a general category/era/mechanic classifier;
- zone analysis: nineteen semantic zones are declared by the resolved template,
  but only title, HP, and collector number are localized and extracted at
  runtime.

## Not implemented

- grading, condition assessment, authenticity determination, or pricing;
- broad-set accuracy benchmarks and confidence calibration;
- interactive human-review UI;
- standalone `card analyze`, `review export`, and generalized inventory merge
  commands;
- production packaging, CI, signed release, or service deployment.
