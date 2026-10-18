# Pre-Alpha Threat-Control Status

Status: **engineering controls implemented; independent security disposition absent**

Implemented and tested locally:

- loopback-only Compose binding, non-root UID, read-only root filesystem,
  dropped capabilities and no-new-privileges;
- request-size, identifier, idempotency and bounded-capacity controls;
- manifest-only artifact access with digest/length/media type binding, safe
  filename, traversal/symlink confinement and `nosniff` response;
- review writes disabled by default and gated by a runtime-injected bearer token,
  attributable actor, bounded scope, evidence version and optimistic concurrency;
- append-only job transitions, review dispositions and superseding assertions;
- rights/adjudication gating for evaluation fixtures and explicit unsupported
  symbol states;
- automatic confirmation prohibited and measured as a failing policy condition;
- consistent SQLite backup, integrity verification and non-overwriting restore.

Open before RG-4/RG-6:

- independent threat review and authenticated-identity mechanism decision;
- decoder bomb/pixel-cap hardening beyond request length;
- container vulnerability scan and triage for the exact image digest;
- full secret scanner, SBOM/license reconciliation, provenance signing and
  signature verification;
- workload-bound CPU/memory/disk/latency evidence and failure injection;
- encrypted backup, retention/privacy decision and audit-log access policy;
- formal security, licensing and release-authority dispositions.

`scripts/generate_local_security_evidence.py` produces a local CycloneDX-shaped
component inventory, bounded pattern-based secret scan and exact-commit
provenance record. It deliberately reports vulnerability/container scanning as
`EVIDENCE_REQUIRED` when those events have not occurred. Its output is evidence
for review, not security approval or release authorization.
