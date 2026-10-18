# Local Recovery and Operating Envelope

Status: **Pre-Alpha procedure; independent operational acceptance absent**

## Bounded operating profile

- API exposure: loopback only.
- Worker concurrency: `PTCG_JOB_WORKERS=1` by default.
- Active admission limit: `PTCG_MAX_ACTIVE_JOBS=4` by default; excess requests
  receive HTTP 429 and `Retry-After`.
- Request size: 25 MiB by default.
- Evidence, jobs, reviews and assertions are retained. Automatic deletion is
  prohibited until a retention decision replaces
  `RETAIN_UNTIL_EXPLICITLY_GOVERNED`.
- Cancellation is cooperative at ingest, geometry, card, extraction and
  projection checkpoints; completed evidence is not deleted.

These values are safe local defaults, not measured capacity promises.

## Restart and interruption

At startup, admitted jobs are relaunched. Running jobs append
`RECOVERY_REQUIRED` then `ADMITTED` before replay. A recorded cancellation is
completed as `CANCELED`. Terminal success is written only after required
outputs and the run integrity audit pass.

## Backup

Stop or quiesce admission for a release rehearsal, then run:

```bash
ptcg operations backup \
  --job-database .local/jobs/jobs.sqlite3 \
  --review-database .local/reviews/reviews.sqlite3 \
  --output .local/backups/BACKUP_ID

ptcg operations verify-backup .local/backups/BACKUP_ID
```

The SQLite backup API creates consistent copies. The manifest binds length,
SHA-256 and SQLite integrity for each database without exposing absolute host
paths.

## Restore rehearsal

Restore only to a new path, verify SQLite integrity, launch against the restored
copies on a separate local profile, then compare job transitions, review
dispositions, assertion chains and effective inventories. Never overwrite the
source databases during rehearsal. Artifact/run directories are content-bound
and require a separate filesystem snapshot and `ptcg evidence verify` pass.

## Required candidate evidence

Before release qualification, capture admission latency, queue wait, analysis
latency, CPU, peak memory and disk growth for named workloads; cancellation at
OCR/comparison/projection checkpoints; API restart; worker interruption;
corrupt artifact; capacity rejection; backup/restore; and exact environment.
Absent results remain `EVIDENCE_REQUIRED`.
