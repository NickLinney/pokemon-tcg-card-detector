# Pokémon TCG Card Detector

Evidence-preserving, local-first pre-alpha pipeline for decomposing a nine-pocket
binder photograph into ordered card observations, local catalogue candidates,
qualified identification decisions, and inventory exports.

This is an experimental vertical slice. It does **not** claim broad historical
coverage, grading, authentication, production readiness, or reliable automatic
identification beyond measured fixtures. `UNKNOWN`, `AMBIGUOUS`,
`CONFLICTING`, and `INSUFFICIENT_EVIDENCE` are valid results.

## Implemented slice

- deterministic 3x3 page segmentation and normalized 630x880 card crops;
- reversible page, card, and semantic-zone geometry;
- inherited YAML templates for generic, historical Japanese, VS-owner, and
  modern layouts;
- offline Japanese/English OCR with raw and normalized alternatives;
- a read-only SQLite catalogue compiled from a pinned local TCGdex snapshot;
- candidate retrieval, discriminator planning, conservative evidence fusion,
  and explicit review states;
- non-overwriting evidence packages and JSONL, CSV, and SQLite inventory output;
- JSON Schemas for reference, observation, decision, and inventory records.

## Local setup

Python 3.12 is required. The commissioned run used a project-local virtual
environment and the exact versions in `requirements.lock.txt`.

```bash
python3.12 -m venv ../.venv
../.venv/bin/python -m pip install -r requirements.lock.txt
```

EasyOCR model weights must be stored beneath `../.models/easyocr`. They are not
redistributed by this repository. Their observed digests and license caveat are
in `docs/DEPENDENCY-LICENSE-REGISTER.md`.

## Commands

```bash
PYTHONPATH=src ../.venv/bin/python -m ptcg template validate

PYTHONPATH=src ../.venv/bin/python -m ptcg corpus verify \
  ../.local/corpus/tcgdex-v2.48.0-r3.sqlite3

PYTHONPATH=src ../.venv/bin/python -m ptcg page analyze \
  ../binder-ingest-images/samples/000-first-sample.jpeg \
  --database ../.local/corpus/tcgdex-v2.48.0-r3.sqlite3 \
  --output ../.local/runs

PYTHONPATH=src ../.venv/bin/python -m pytest -q
```

Every analysis allocates a new run directory; prior evidence is not overwritten.
The current commissioned evidence is documented in
`docs/SAMPLE-RUN-REPORT.md`.

## Lifecycle

- target: Pre-Alpha 1 vertical slice;
- current disposition: implemented and locally validated, not released;
- publication: pending repository credentials;
- promotion: blocked until independent QA/security/release acceptance exists.
