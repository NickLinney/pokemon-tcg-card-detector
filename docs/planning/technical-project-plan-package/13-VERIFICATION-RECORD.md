# Verification Record

**Executed:** 2026-10-17/18 America/New_York

**Scope:** artifacts and reversible implementation changes in this delivery

| Check | Result | Evidence |
|---|---|---|
| Python tests | PASS | `17 passed in 2.08s` |
| CLI entry | PASS | `python -m ptcg --help` and template validation |
| API entry | PASS | `python -m ptcg.api --help`; Flask test client |
| Template registry | PASS | seven templates; zero validation findings |
| OpenAPI serialization | PASS | PyYAML parse |
| Compose model | PASS | `docker compose config --quiet` |
| CPU-only image correction | PASS in first corrected build | build completed as image `b843794c…`; avoided CUDA packages |
| Container CLI | PASS | disposable container validated seven templates |
| Gunicorn factory | PASS | disposable `--check-config` run |
| Live API health/readiness | PASS on the first corrected image | `/healthz` 200 and `/readyz` 200 on loopback |
| Exact runtime-lock final rebuild | ENVIRONMENT BLOCKED | Docker storage exhausted during package installation; final Dockerfile was optimized to avoid duplicate dependency resolution, but was not rebuilt after that last correction |
| Diff whitespace | PASS | `git diff --check` |

The exact-lock rebuild failure is not a code/test failure and does not justify a
successful final-image claim. Broad Docker pruning was deliberately not used
because it could delete unrelated user caches and images. Final container
release evidence therefore requires a clean builder or separately authorized
project-specific cache cleanup followed by build, smoke, SBOM and scan.

No production-readiness, lifecycle-promotion or release disposition was
performed by these checks.
