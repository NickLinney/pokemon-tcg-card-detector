# Operations, Observability, Recovery and SLOs

## Operational model

Production uses stateless API processes, durable jobs, separately scalable
workers, read-only versioned dependencies, append-only evidence storage and a
transactional job/review metadata store. SQLite remains supported for local and
single-operator profiles; concurrent production review/job control requires a
server database selected through an ADR.

## Signals

Every log, metric and trace carries `request_id`, `job_id`, `run_id`, component,
code version and dependency-manifest digest. Never log raw image bytes, OCR text
by default, credentials, or full local paths when they expose user data.

Required metrics: accepted/rejected jobs; state duration; retry/cancel/failure;
queue age; cards/zones processed; abstention and review rates; OOD/template
distribution; extractor failure; corpus/template/model version; CPU/GPU/memory;
storage growth; API/error latency; lineage completeness; and stale-evidence
count. Drift signals are operational alerts, not automatic truth updates.

## Candidate service objectives

These are planning candidates and require baseline/owner approval:

| Objective | Candidate | Measurement |
|---|---|---|
| API availability | 99.5% monthly for controlled production | non-maintenance successful health/readiness |
| job durability | no acknowledged job lost | persisted acceptance vs terminal/cancelled records |
| evidence integrity | 100% manifest verification | scheduled digest audit |
| lineage completeness | 100% required links for terminal jobs | schema/query audit |
| recovery | RPO 0 for acknowledged metadata; RPO ≤24h for rebuildable corpus/index | restore drill |
| service restore | RTO ≤4h controlled deployment | timed exercise |
| analysis latency | set per hardware/workload after WP-050 | p50/p95/p99 by page/card profile |

Accuracy/model objectives live in the evaluation policy, not availability SLOs.

## Failure handling

- Validate and persist before acknowledging a job.
- Retry only classified transient operations with bounded backoff.
- Resume from immutable stage checkpoints; do not duplicate terminal artifacts.
- Quarantine corrupt input/dependencies and preserve failure evidence.
- Open a circuit or reject with capacity information before resource collapse.
- A dependency version mismatch stops execution or selects an explicitly
  compatible version; it never silently continues.

## Runbook minimum

Startup: verify image digest, SBOM/signature, configuration, corpus, registry,
models, write roots and readiness. Incident: preserve request/run IDs, classify
safety/integrity/availability, stop affected confirmation policy if necessary,
snapshot manifests, communicate scope, recover from verified checkpoint, and
record follow-up fixture. Shutdown: drain API, checkpoint/cancel workers,
verify stores and preserve audit records.

## Backup and disaster recovery

Use encrypted, versioned backups with independent access. Quarterly restore
tests rebuild corpus/index, restore job/review metadata and sample evidence,
then verify hashes and replay a sealed fixture. A backup that has not been
restored and verified is not recovery evidence.
