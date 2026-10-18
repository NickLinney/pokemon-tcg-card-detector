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

## Release-blocking gates

- RG-0 through RG-6 lack the full actual role dispositions required by the
  release plan.
- Rights-qualified evaluation fixtures and accepted metric thresholds are
  absent.
- Exact-image vulnerability/container scanning and independent security,
  QA/evaluation, licensing and release decisions are absent.
- Docker image evidence is not current because the host Docker store has a
  previously observed capacity blocker; no broad destructive prune is
  authorized.
- Remote credentials/publication evidence remains unavailable.

Accordingly, no release tag, GitHub prerelease, lifecycle promotion, production
merge or robust-accuracy claim is eligible. Local `test`, `staging` and
`release/0.2.0` branch pointers are environment/candidate ledgers only and do
not themselves satisfy a gate.
