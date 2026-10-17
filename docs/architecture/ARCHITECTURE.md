# Architecture

The vertical slice is a local, staged evidence pipeline:

`capture -> segment -> normalize -> template -> observe -> candidates -> targeted discriminator -> fuse -> decide -> inventory`

## Truth boundaries

- **Reference truth:** immutable raw TCGdex source payloads plus explicitly
  mapped catalogue fields in the compiled SQLite store.
- **Observation truth:** source/crop/zone geometry, quality measurements, raw
  OCR alternatives, parsed values, and visual features.
- **Decision truth:** ranked candidates, contradictions, confidence, state, and
  review requirement. A decision never mutates reference or observation truth.

## Runtime components

`vision.py` derives the 3x3 geometry from yellow-border projections and writes
normalized crops. `template_registry.py` resolves inherited YAML layouts.
`ocr.py` preserves raw EasyOCR results and typed parsers. `store.py` performs
read-only local queries. `candidates.py` scores text, structured data, and
structural hints. `imagematch.py` offers pHash/ORB evidence but explicitly does
not prove a printing. `decision.py` requires multiple strong evidence families,
margin, quality, and no contradiction before confirmation. `pipeline.py`
serializes the evidence and inventory products without overwriting old runs.

## Data products

Each run contains page geometry, nine normalized crops, zone crops, one evidence
JSON document per pocket, a page summary, and inventory exports in JSONL, CSV,
and SQLite. Schemas live in `schemas/`. Local corpus, model, media, and run files
remain outside Git.

## Trust and failure model

The process is offline after dependencies/models are present. Input hashes and
pinned corpus identity establish provenance, not correctness. Missing reference
images, OCR errors, source-data defects, or conflicting signals reduce the
decision state rather than being silently coerced into an identity.
