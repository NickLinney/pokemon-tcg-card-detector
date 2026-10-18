# Interface Contracts

## Implemented CLI contract

```text
ptcg corpus ingest SOURCE --database DB --manifest MANIFEST
ptcg corpus verify DB
ptcg template validate [--root TEMPLATE_ROOT]
ptcg page analyze IMAGE --database DB --output DIR
                  [--templates TEMPLATE_ROOT] [--ocr easyocr|none]
                  [--download-ocr-models]
```

Commands write JSON to stdout; diagnostics must move to stderr as the CLI
contract matures. Current success is exit `0`; template validation findings are
exit `1`; argparse misuse is exit `2`. Before Alpha, standardize: `0` success,
`2` invalid request, `3` configuration/dependency unavailable, `4` completed
with unresolved/review-required results, `5` integrity failure, `10` internal
failure. Never use a nonzero exit merely because an identity abstained unless
the caller requested a confirmation-only policy.

## Target CLI additions

- `ptcg run status|resume|cancel RUN_ID`
- `ptcg batch analyze MANIFEST --jobs N`
- `ptcg evaluate run BENCHMARK --policy POLICY`
- `ptcg review export|import`
- `ptcg evidence verify RUN_ID`
- `ptcg config validate|show --effective --redact`

Every mutating command supports `--dry-run` where meaningful, an idempotency
key, machine-readable JSON and an explicit output root.

## Implemented HTTP contract

`openapi.yaml` is the machine-readable contract for:

- `GET /healthz`: process is alive; does not assert dependency readiness.
- `GET /readyz`: corpus, templates, paths and OCR configuration are usable.
- `POST /v1/pages/analyze`: multipart image, synchronous local Pre-Alpha run.

The upload limit defaults to 25 MiB. Allowed suffixes are JPEG, PNG, TIFF and
WebP; suffix acceptance does not replace content decoding validation. Uploaded
source evidence is retained under a request ID. Validation errors contain no
stack trace; unexpected errors return an opaque request ID.

## Target production job contract

| Method/path | Behavior |
|---|---|
| `POST /v1/analysis-jobs` | validate, persist source, return `202` and immutable job ID |
| `GET /v1/analysis-jobs/{id}` | state, progress, version manifest and terminal links |
| `POST /v1/analysis-jobs/{id}:cancel` | request cancellation; preserve evidence |
| `GET /v1/runs/{id}/evidence` | authorized manifest/download enumeration |
| `POST /v1/reviews` | append attributed review action with optimistic concurrency |

Required HTTP semantics: idempotency key, correlation ID, authenticated actor,
request-size and rate limits, problem-details errors, pagination, versioned
media types, audit record, and explicit `Retry-After` for capacity rejection.

## Configuration contract

| Variable | Required | Default | Secret | Meaning |
|---|---:|---|---:|---|
| `PTCG_PROJECT_ROOT` | container | discovered Project root | no | sole writable authority root |
| `PTCG_DATABASE` | API | none | no | pinned verified SQLite corpus |
| `PTCG_TEMPLATE_ROOT` | no | repository templates | no | versioned registry |
| `PTCG_OUTPUT_ROOT` | no | Project `.local/runs` | no | non-overwriting evidence runs |
| `PTCG_UPLOAD_ROOT` | no | Project `.local/uploads` | no | retained request sources |
| `PTCG_MODEL_DIRECTORY` | no | Project `.models/easyocr` | no | preprovisioned model weights |
| `PTCG_OCR` | no | `easyocr` | no | `easyocr` or `none` |
| `PTCG_DOWNLOAD_OCR_MODELS` | no | `false` | no | explicit network/model acquisition switch |
| `PTCG_MAX_CONTENT_LENGTH` | no | 26214400 | no | HTTP body ceiling |

Future credentials must come from a secrets provider or mounted secret, never
source control, Compose literals, logs or evidence payloads. Configuration is
validated at startup and its non-secret effective digest is attached to runs.

## Compatibility

Schemas and APIs use semantic versions. Additive optional fields are backward
compatible; removals, meaning changes and tighter validation require a major
version and migration. Template/model/policy changes always produce new run
evidence rather than rewriting old results.
