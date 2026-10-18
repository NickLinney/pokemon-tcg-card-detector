# Pokémon TCG Card Detector

Evidence-preserving, local-first pre-alpha pipeline for decomposing a nine-pocket
binder photograph into ordered card observations, local catalogue candidates,
qualified identification decisions, and inventory exports.

This is an experimental vertical slice. It does **not** claim broad historical
coverage, grading, authentication, production readiness, or reliable automatic
identification beyond measured fixtures. `UNKNOWN`, `AMBIGUOUS`,
`CONFLICTING`, and `INSUFFICIENT_EVIDENCE` are valid results.

## Implemented slice

- deterministic 3x3 page segmentation plus an explicitly qualified full-frame
  single-card fallback, producing normalized 630x880 card crops;
- reversible page, card, and semantic-zone geometry;
- inherited YAML templates for generic, historical Japanese, VS-owner, and
  modern layouts;
- compiled template/zone registry coverage with reproducible digest and
  semantic-family, cardinality, applicability, and presence-state contracts;
- hierarchical, top-k template hypotheses with explicit uncalibrated/OOD and
  `UNKNOWN_FAMILY` states;
- a separate observation for every declared zone, with immutable prior crops
  and provisional image-edge localization proposals where supported;
- offline Japanese/English OCR with raw and normalized alternatives;
- a read-only SQLite catalogue compiled from a pinned local TCGdex snapshot;
- candidate retrieval, discriminator planning, conservative evidence fusion,
  and explicit review states;
- sealed run manifests, append-only lifecycle transitions, idempotent completed
  requests, and SHA-256 content-addressed evidence with an integrity auditor;
- non-overwriting evidence packages and proposal-only JSONL, CSV, and SQLite
  inventory output;
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
  --output ../.local/runs \
  --idempotency-key operator-request-001

PYTHONPATH=src ../.venv/bin/python -m ptcg evidence verify \
  ../.local/runs/RUN_ID

PYTHONPATH=src ../.venv/bin/python -m pytest -q
```

The local review workflow is also keyboard-operable through the same core. It
requires an explicit actor and authority scope and preserves the evidence
version and prior-assertion token:

```bash
PYTHONPATH=src ../.venv/bin/python -m ptcg review list \
  --database ../.local/reviews/reviews.sqlite3 --state required

PYTHONPATH=src ../.venv/bin/python -m ptcg review show REVIEW_ID \
  --database ../.local/reviews/reviews.sqlite3

PYTHONPATH=src ../.venv/bin/python -m ptcg inventory export COLLECTION_ID \
  --database ../.local/reviews/reviews.sqlite3 \
  --output ../.local/effective-inventory/EXPORT_ID
```

`review decide` supports the same actions as the HTTP contract. CLI output
always includes content-addressed disposition identity; the UI/CLI is not the
system of record.

The same analysis use case is available to Python callers through
`ptcg.service.analyze_page_request`. An optional local Flask adapter is installed
with the API extra:

```bash
../.venv/bin/python -m pip install -e '.[api]'
PTCG_DATABASE=../.local/corpus/tcgdex-v2.48.0-r3.sqlite3 \
  PYTHONPATH=src ../.venv/bin/python -m ptcg.api
```

It exposes health/readiness, the primary durable `/v1/analysis-jobs` workflow,
manifest-backed run/artifact downloads, review, and effective-inventory APIs.
The synchronous `/v1/pages/analyze` endpoint remains deprecated compatibility
surface only. Review writes are disabled unless `PTCG_REVIEW_TOKEN` is set and
then require the bearer token plus explicit actor and authority-scope headers.
The service remains loopback-only Pre-Alpha integration, not a shared network
or production service.

## Containers

One image supports both transports. The Compose API is published on loopback:

```bash
docker compose build
docker compose up api
docker compose run --rm cli template validate --root /opt/app/templates
```

For local review writes, inject the token at runtime rather than storing it in
Compose or Git:

```bash
PTCG_REVIEW_TOKEN='local-secret-from-approved-store' docker compose up api
```

The production-delivery plan, explicit nonclaims, work packages and release
gates are in
[`docs/planning/technical-project-plan-package/README.md`](docs/planning/technical-project-plan-package/README.md).

Every analysis allocates a new run directory; prior evidence is not overwritten.
When an idempotency key is supplied, the same completed manifest returns the
same run. Automatic confirmation is disabled while calibration remains
`EVIDENCE_REQUIRED`.
The latest governed implementation reconciliation is in
[`docs/execution/production-plan-execution-2026-10-17/README.md`](docs/execution/production-plan-execution-2026-10-17/README.md).
The current commissioned evidence is documented in
`docs/SAMPLE-RUN-REPORT.md`.

## Lifecycle

- target: Pre-Alpha 1 vertical slice;
- current disposition: implemented and locally validated, not released;
- publication: pending repository credentials;
- promotion: blocked until independent QA/security/release acceptance exists.
