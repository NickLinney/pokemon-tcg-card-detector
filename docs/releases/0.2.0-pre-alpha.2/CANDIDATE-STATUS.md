# `0.2.0-pre-alpha.2` Candidate Status

Status: **ENGINEERING IMPLEMENTED / RELEASE NOT AUTHORIZED**

The feature branches for US-001/002, US-010–012, US-020/021, US-030–033,
US-040–044 and US-050–052 are integrated through `dev` with traceable
non-squash merges. A repeatable local UAT harness covers asynchronous
submission, durable status, sealed artifact enumeration/download, digest
parity, attributable review and effective projection.

The harness intentionally uses `LEAVE_UNRESOLVED`. It cannot pass the finalized
identity portion of UAT-14 without a rights-qualified, adjudicated truth record
for the supplied sample. It must not substitute a guessed identity merely to
make the workflow green.

## Current exact-candidate evidence

The `dev`, `test`, and `staging` ledgers were promoted from one exact source
history and exercised against the supplied binder sample. The qualified UAT
result records 14 sealed artifacts, matching effective-inventory digests, the
durable job-state sequence, and an attributable `LEAVE_UNRESOLVED` review. The
repository suite passed 78 tests. The containerized CLI reports
`0.2.0-pre-alpha.2`; the packaged registry validates seven templates and 19
semantic zones; and the HTTP `/healthz` and `/readyz` probes pass on the exact
locally built image.

Local supply-chain evidence binds the source commit and image digest, emits a
CycloneDX SBOM and provenance, and records a passing secret scan. Vulnerability
scanning remains `EVIDENCE_REQUIRED`; none of this evidence is an independent
security disposition or release authorization.

## Release-blocking gates

- RG-0 through RG-6 lack the full actual role dispositions required by the
  release plan.
- Rights-qualified evaluation fixtures and accepted metric thresholds are
  absent.
- Exact-image vulnerability/container scanning and independent security,
  QA/evaluation, licensing and release decisions are absent.
- Remote credentials/publication evidence remains unavailable.

Accordingly, no release tag, GitHub prerelease, lifecycle promotion, production
merge or robust-accuracy claim is eligible. Local `test`, `staging` and
`release/0.2.0` branch pointers are environment/candidate ledgers only and do
not themselves satisfy a gate.
