# Verification Record

Executed against pipeline `pre-alpha-evidence-architecture-v7` on
2026-10-17/18 America/New_York.

| Check | Result | Observed evidence |
|---|---|---|
| Automated tests | PASS | 35 passed |
| JSON Schema definitions | PASS | all Draft 2020-12 schemas structurally valid |
| Runtime contract instances | PASS | artifact, run manifest, template classification, and all zone observations validate |
| Template registry | PASS | 7 templates, 19 zones, 5 anchors, zero findings, digest `56aa7910…` |
| Corpus integrity | PASS | SQLite integrity `ok`; 42,055 cards; zero import errors; digest `23243e4a…` |
| Commissioned-page smoke | QUALIFIED PASS | 9 cards, 171 zone records, 139 provisional pixel proposals, 9 ambiguous decisions |
| Run lifecycle | PASS | 10 valid append-only transitions; terminal state `REVIEW_REQUIRED` |
| Evidence audit | PASS | 198 stored artifacts verified; 198 references resolved; zero findings |
| Idempotent replay | PASS | repeated key re-audited integrity, then returned the same completed run |
| Python environment | PASS | `pip check`: no broken requirements |
| OpenAPI document | PASS | YAML parse; bounded optional `Idempotency-Key` contract |
| Compose model | PASS | `docker compose config --quiet` |
| Plan-package checksums | PASS | all package files verified after OpenAPI update |
| Git whitespace | PASS | `git diff --check` |
| OCI image rebuild | NOT REPEATED | prior host Docker-storage blocker remains; no unrelated user data was pruned |

The commissioned smoke used OCR mode `none` to make network/model independence
explicit. Accordingly, 117 OCR-capable zone attempts returned `NO_SIGNAL`, 9
artwork descriptors returned `SUCCEEDED`, and 45 symbol-only zones returned
`UNSUPPORTED`. Those are expected qualified states, not extraction-accuracy
evidence.

No test in this record constitutes taxonomy acceptance, threshold acceptance,
security approval, production readiness, deployment, publication, or release.
