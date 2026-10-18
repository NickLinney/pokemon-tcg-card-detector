# Release Backlog and Traceability — `0.2.0-pre-alpha.2`

Status: **PLANNED / NOT IMPLEMENTED / NOT RELEASED**

## 1. Outcome hierarchy

| Actor | Use case | Measurable release outcome |
|---|---|---|
| Collector/operator | Submit a binder page | Validated collection, binder and page context produces a durable job within the admission budget |
| Collector/operator | Follow analysis | Job state, progress, cancellation and replay survive process restart |
| Collector/operator | Retrieve results | Manifest-listed CSV and evidence are enumerable and downloadable with matching digests |
| Reviewer | Resolve ambiguity | An authenticated, attributable review can select, reject, correct, recapture or retain uncertainty |
| Data steward | Preserve truth history | Review assertions can be superseded without altering original observations or decisions |
| Evaluator | Measure detection and identification | Rights-qualified fixtures yield reproducible template, zone, extraction, retrieval and decision scorecards |
| Maintainer | Operate one application core | Python API, CLI, HTTP and container profiles remain behaviorally equivalent |
| Release authority | Decide on an exact candidate | Commit, image, SBOM, provenance, tests, risks and dispositions are bound in one evidence packet |

## 2. Epic backlog

### EP-00 — Release identity and governed contracts

#### US-001 — Canonical release identity

As a maintainer, I need one canonical product identity so that every executable,
contract and release artifact refers to the same candidate.

Acceptance criteria:

- Canonical SemVer is `0.2.0-pre-alpha.2`; lifecycle is `PRE_ALPHA`.
- The repository adaptation explains that numeric core progression and lifecycle
  classification are independent.
- Runtime `--version`, API metadata, manifests, image labels, release notes and
  tag are checked for consistency.
- Python distribution metadata uses documented PEP 440 mapping `0.2.0.dev2`
  without replacing the canonical SemVer.

Trace: CAP-001, CAP-015; RG-0; UAT provenance gap.

#### US-002 — Versioned job, context, artifact and review schemas

As an integrator, I need machine-valid contracts so that adapters cannot invent
different meanings for the same workflow.

Acceptance criteria:

- JSON Schema/OpenAPI objects cover job state, context, artifact descriptor,
  review case, disposition, supersession and effective projection.
- Every object carries schema version and stable identifier rules.
- Compatibility fixtures exercise prior UAT evidence and rejected malformed
  inputs.

Trace: CAP-001, CAP-002, CAP-013; RG-1.

### EP-01 — Durable analysis jobs and collection context

#### US-010 — Context-aware asynchronous submission

As a collector, I want to submit an image with collection, binder and page
context and receive a job ID without waiting for analysis.

Acceptance criteria:

- `POST /v1/analysis-jobs` validates media and opaque context identifiers.
- A valid request returns `202` and status link within the accepted local
  admission budget; pipeline work executes outside the request thread.
- The sealed input digest and exact context appear in all projections.
- Repeating an idempotency key with the same input returns the same job; a
  conflicting input is rejected.

Trace: CAP-001, CAP-002, CAP-015; UAT-03, UAT-06, UAT-12; CIO increment 2/5.

#### US-011 — Durable job state machine

As an operator, I need requested, admitted, running, terminal and recovery states
to remain truthful across restarts.

Acceptance criteria:

- Transitions are append-only, schema-valid and idempotent.
- Restart restores pending/running work to a documented safe state.
- Terminal states distinguish succeeded, failed, canceled and rejected.
- A job never reports success before its manifest and required artifacts seal.

Trace: CAP-001, CAP-002, CAP-015; RG-1/RG-3.

#### US-012 — Cancellation and capacity behavior

As an operator, I need bounded cancellation and overload behavior so local
resources remain controllable.

Acceptance criteria:

- Cancellation is idempotent and preserves all completed evidence.
- Admission limits return a bounded retry response rather than exhausting the
  host.
- Tests cover cancellation during OCR, comparison and inventory projection.

Trace: CAP-001, CAP-015; CIO increment 5.

### EP-02 — Run and artifact delivery

#### US-020 — Enumerate a run and its artifacts

As a collector, I want to see the completed run and downloadable outputs without
requiring host filesystem access.

Acceptance criteria:

- `GET /v1/runs/{run_id}` returns bounded summary, state and permitted links.
- `GET /v1/runs/{run_id}/artifacts` returns manifest-backed descriptors only.
- Unknown run, unsealed manifest and disallowed artifact states are distinct.

Trace: CAP-002, CAP-015; UAT-15; CIO increment 1.

#### US-021 — Download exact CSV and evidence

As a collector, I want to download the application-created inventory proposal
and evidence and verify their identity.

Acceptance criteria:

- Artifact IDs resolve through the manifest, never through caller paths.
- Responses carry media type, byte length, SHA-256, safe filename and range
  semantics where supported.
- Downloaded `inventory.csv` digest equals the sealed manifest digest.
- Traversal, symlink escape, unlisted file and content-type confusion tests pass.

Trace: CAP-002, CAP-015; UAT-04, UAT-11, UAT-15.

### EP-03 — Review, supersession and effective inventory

#### US-030 — Review-required queue

As a reviewer, I want a paginated queue of ambiguous pockets with the relevant
evidence and candidate explanations.

Acceptance criteria:

- Queue selection is derived from decision truth, not mutable labels.
- Read model links normalized image, template hypotheses, zone observations,
  candidates, scores and limitations without altering source evidence.
- Large artifacts are links, not embedded unbounded payloads.

Trace: CAP-006–013; UAT-09/UAT-10; CIO increment 3.

#### US-031 — Attributable review disposition

As an authorized reviewer, I want to select a candidate, reject candidates,
correct a field, request recapture or retain uncertainty.

Acceptance criteria:

- Each disposition records actor, authority scope, reason, timestamp, evidence
  version and expected prior assertion.
- Identity and printing decisions remain separate.
- Anonymous writes and stale optimistic-concurrency tokens are rejected.
- Selecting a candidate absent from the evidence requires an explicit manual
  assertion type and rationale, not a rewritten model result.

Trace: CAP-013; UAT-14; RG-1/RG-3.

#### US-032 — Supersession and effective projection

As a data steward, I want corrections to supersede prior assertions while
retaining an auditable history.

Acceptance criteria:

- No observation, automated decision or prior human assertion is overwritten.
- A deterministic projector produces one effective state per stable location.
- CSV, JSONL and SQLite projections are canonical-equivalent.
- Conflicting concurrent review and replay produce no duplicate effective state.

Trace: CAP-013; UAT-07/UAT-08/UAT-14.

#### US-033 — Minimal accessible local review surface

As a reviewer, I need a usable local interface for the review workflow.

Acceptance criteria:

- CLI is complete; a small Flask/FastAPI-rendered interface may be added when it
  reduces review error and uses the same application service.
- Keyboard operation, visible state/error feedback and evidence provenance are
  testable.
- UI state never becomes the system of record.

Trace: CAP-013, CAP-015; product usability gap.

### EP-04 — Measured semantic evidence uplift

#### US-040 — Rights-qualified ground-truth registry

As an evaluator, I need fixtures with provenance, rights and adjudication so
that quality claims are reconstructable.

Acceptance criteria:

- Fixture manifest records source, permitted use, content digest, split and
  annotation/adjudication state.
- Train/development/evaluation splits are leakage checked.
- Unresolved rights or truth state excludes the fixture from claimed metrics.

Trace: CAP-014; CIO increment 4; RG-2.

#### US-041 — Template classification scorecard

As an evaluator, I want template-family and subtype metrics by relevant stratum.

Acceptance criteria:

- Report covers family top-k recall, subtype accuracy, abstention and confusion.
- Template registry/version and exact fixture split are bound to results.
- Sparse or absent strata are marked `EvidenceRequired`, never imputed.

Trace: CAP-006, CAP-007, CAP-014; architecture template requirement.

#### US-042 — Semantic-zone localization scorecard

As an evaluator, I want per-zone localization and presence metrics so that the
system can prove it found the intended information zones.

Acceptance criteria:

- Metrics include presence precision/recall, IoU or keypoint tolerance,
  localization status and fallback usage by zone type/template stratum.
- The report distinguishes declared, independently localized, inherited,
  unsupported and no-signal zones.

Trace: CAP-007, CAP-008, CAP-014; UAT 171 zones/139 independently localized.

#### US-043 — Typed extraction and symbol-provider baseline

As an evaluator, I need typed field and symbol extraction measured separately
from OCR text so unsupported evidence cannot disappear in aggregates.

Acceptance criteria:

- Metrics cover normalized exact/field accuracy, unsupported, no-signal and
  extraction-failure rates by zone type.
- Provider interfaces exist for text, numeric and supported symbol families.
- Set, rarity and energy symbol baselines are enabled only for approved fixture
  strata and return typed uncertainty outside them.

Trace: CAP-009, CAP-014; UAT extraction states and 45 unsupported zones.

#### US-044 — Candidate and decision safety scorecard

As a product owner, I need top-k recall, unresolved behavior and false-
confirmation measurements before considering automated confirmation.

Acceptance criteria:

- Candidate recall, exact identity, exact printing, unresolved and false-
  confirmation rates are reported independently.
- `CONFIRMED_AUTOMATIC` remains disabled and has a failing policy test.
- Threshold adoption requires a separate recorded decision with held-out data.

Trace: CAP-010–012, CAP-014; RG-2/RG-4.

### EP-05 — Hardening and evidence-bearing release

#### US-050 — Python, CLI, HTTP and container parity

As a maintainer, I need all execution profiles to invoke the same application
core and preserve equivalent output semantics.

Acceptance criteria:

- Contract fixtures pass through Python API, CLI and HTTP adapters.
- Docker and Docker Compose execute without host dependency installation.
- Runtime stays non-root, loopback-first and offline for routine analysis.

Trace: CAP-001, CAP-015; original execution-profile requirement.

#### US-051 — Recovery, load and operating-envelope evidence

As an operator, I need tested limits and recovery procedures.

Acceptance criteria:

- Restart, interruption, backup/restore and corrupt-artifact rehearsals pass.
- Page latency, queue wait, CPU, memory and disk are captured by workload.
- Capacity rejection and retention behavior are documented and testable.

Trace: CAP-015; CIO increment 5; RG-4.

#### US-052 — Exact-candidate security and supply-chain packet

As security/release authority, I need reviewable evidence for the exact bytes.

Acceptance criteria:

- Threat controls, negative tests, secret scan, dependency/license report,
  SBOM, vulnerability report and provenance bind to commit and OCI digest.
- Critical/high findings require recorded remediation or authorized acceptance.
- Corpus, model, template, policy and media-rights versions are included.

Trace: CAP-002, CAP-015; RG-4/RG-6.

#### US-053 — Governed Pre-Alpha release event

As release authority, I need a reproducible and truthful `0.2.0-pre-alpha.2`
release without an implied Alpha promotion.

Acceptance criteria:

- Every required story and gate has an actual disposition for one exact
  candidate.
- Version files, changelog, release notes, migration notes and tag agree.
- Annotated tag is `0.2.0-pre-alpha.2`; release is visibly marked prerelease.
- Failure or deferral leaves the candidate unreleased and preserves evidence.

Trace: CAP-015; RG-0–RG-6; NickLinneyDev release invariant.

## 3. Dependency order

`US-001 → US-002 → US-010 → US-011 → US-020 → US-021 → US-030 →`
`US-031 → US-032 → US-053`

Parallel joins:

- `US-012` joins before US-051.
- `US-040 → US-041/042/043 → US-044` joins before RG-4 and US-053.
- `US-050 → US-051/052` joins before US-053.
- US-033 may proceed after US-030/031 contracts stabilize and joins before UAT.

## 4. Release coverage and deferral rule

All listed stories are required for the target release unless RG-0 records a
scope change and re-runs dependency, risk and UAT coverage analysis. A story may
not be labeled complete from file existence alone. If any critical-path story
is deferred, `0.2.0-pre-alpha.2` is not released; engineering may continue under
an explicitly versioned development state without inventing acceptance.
