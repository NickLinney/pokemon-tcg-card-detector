# Software Release Lifecycle Development Plan — `0.2.0-pre-alpha.2`

Status: **CANDIDATE PLAN / PRE-ALPHA BASELINE / RELEASE NOT AUTHORIZED**

Plan-package version: `0.2.0-pre-alpha.2`

Target product release: `0.2.0-pre-alpha.2`

Baseline revision: `6f4003150d7703f87ee07dd23a810afd062b033f`

## 1. Executive product decision

The next bounded product increment will be planned as a **reviewable,
asynchronous evidence workflow**. It will convert the demonstrated local
proposal generator into a coherent Pre-Alpha 2 surface in which a collector can
submit a page with real collection context, follow a durable job, retrieve the
application-created evidence and CSV, and route ambiguous results to an
attributable reviewer whose append-only decision produces a deterministic
effective inventory projection.

The release also establishes the first adjudicated evaluation baseline for the
existing template, zone, extraction and candidate stages. That baseline is for
measurement and regression; it is not permission to turn on automatic
confirmation.

This is the smallest release outcome that directly closes the user-workflow
failures in the container UAT while advancing CAP-001, CAP-013, CAP-014 and
CAP-015 without pretending to complete the full robust architecture.

## 2. Governed mandate and disposition

### ThinkLikeACIO classification

| Action | Classification | Decision |
|---|---|---|
| Interpret UAT feedback and product intent | `CIO_DECIDE` | authorized for this plan |
| Select release scope and target minor version | `CIO_DECIDE` | target `0.2.0-pre-alpha.2`; lifecycle remains Pre-Alpha |
| Inspect project, UAT and governance inputs | `AUTHORIZED_EXECUTION` | completed read-only |
| Create versioned planning artifacts under `Project/` | `AUTHORIZED_EXECUTION` | authorized and reversible |
| Implement stories in this plan | future `AUTHORIZED_EXECUTION` | requires an implementation commission or continuation under existing authority |
| Claim QA, security, evaluation or release approval | `ABSTAIN` | independent dispositions are absent |
| Tag, publish or promote the release | `ESCALATE` | Release Authority plus repository access required |

### SSAC disposition

At `PLAN_OR_STRATEGY_SELECTION`, the deterministic advisory matched RI-02 and
SA-02 and returned `ADMIT_QUALIFIED`: the mutually dependent review, inventory,
evaluation and API capabilities may co-evolve through bounded contracts.

At `CANDIDATE_DISPOSITION`, a hypothetical release transition matched ST-06,
ST-07 and CL-03 and returned `ESCALATE`: plan construction does not authorize
promotion, and non-promotion remains a valid outcome.

## 3. Evidence-bound current state

### UAT baseline

The inspected ZIP has SHA-256
`95f9cfb4ac81540d677e17be2b5085440bbc3ab341aa431809747d48b860298f`.
The archive passed `unzip -t`, and all 65 members listed in the final checksum
manifest verified from the package parent directory.

| Observation | Bound result |
|---|---|
| UAT disposition | `QUALIFIED_ACCEPTANCE` |
| Tested commit | `6f4003150d7703f87ee07dd23a810afd062b033f` |
| Pipeline | `pre-alpha-evidence-architecture-v7` |
| Application run | `run-5cc94e4d838f-f4e72c50` |
| Health/readiness | HTTP 200 / HTTP 200 |
| Inventory exports | CSV, JSONL and SQLite agree; 9 rows |
| Identity state | 9 `AMBIGUOUS`; 0 canonical identities |
| Zone records | 171 declared and recorded; 139 independently localized |
| Extraction states | 64 `SUCCEEDED`, 62 `NO_SIGNAL`, 45 `UNSUPPORTED` |
| Evidence integrity | 198/198 artifacts; `PASS` |
| Idempotent replay | same run; verified |
| Repository suite | 35 tests passed |
| UAT-14 | `FAIL` — finalized inventory unrealized |
| UAT-15 | `NOT_IMPLEMENTED` — no HTTP artifact retrieval |

### Confirmed product gaps

1. Ambiguous decisions cannot be resolved inside the application.
2. A user cannot enumerate a run or download the CSV/evidence over HTTP.
3. Collection, binder and page context are fixed sample values rather than a
   validated user contract.
4. Analysis is synchronous and took 140 seconds in the full UAT harness.
5. Accuracy, calibration and per-stratum behavior remain unmeasured.
6. Forty-five symbol-only zone attempts are explicitly unsupported, and
   template/localization outputs remain uncalibrated hypotheses.
7. Version identity is inconsistent: `pyproject.toml` says `0.0.0`, the
   planning OpenAPI says `0.1.0-pre-alpha.2`, and evidence-package versions are
   not product releases.
8. The active branch has no product release tag; remote publication authority
   and credentials are not evidenced.

## 4. Corrected version and lifecycle strategy

### 4.1 Version decision and authority reconciliation

The project-specific target is `0.2.0-pre-alpha.2`. This is a SemVer-valid
pre-release identifier in which two independent dimensions are communicated:

- `0.2.0` identifies the second pre-1.0 minor capability increment; and
- `pre-alpha.2` identifies the retained experimental maturity and the second
  Pre-Alpha release sequence in this project lineage.

The earlier interpretation that every Pre-Alpha artifact must keep a `0.0.0`
core version was rejected after authority reconciliation. The Development
Lifecycle Maturity standard expressly says that lifecycle classification and
numeric progression are distinct and that the standard does not define full
SemVer syntax. The generic/inherited `VERSIONING.md` text that illustrates
`0.0.0-pre-alpha.N` conflicts with the established project lineage
(`0.1.0-pre-alpha.1`, `0.1.0-pre-alpha.2`) and with the Commissioner's explicit
project-specific clarification. Under the execution prompt's conflict rule,
the express project objective and Commissioner clarification control. R0 must
record this repository adaptation so future tooling cannot repeat the error.

This version decision does **not** promote the product to Alpha. Release
authority and lifecycle authority remain orthogonal.

### 4.2 Pre-Alpha commitment boundary

The Pre-Alpha release will promise only this bounded behavior:

> Authorized local evaluators can run the local container, submit authorized
> card/page images, observe durable job state, retrieve evidence-linked proposal
> artifacts, record attributable review dispositions, and export the resulting
> effective local inventory under documented instability and local-only limits.

It will not promise production service, general accuracy, stable APIs,
automatic identity confirmation, printing identification, multi-tenant
security, remote hosting, SLAs or backward compatibility beyond explicitly
listed Pre-Alpha contracts.

### 4.3 Release identity surfaces

| Surface | Required value/control |
|---|---|
| Canonical product/release version | `0.2.0-pre-alpha.2` |
| Python distribution metadata | `0.2.0.dev2`, with an explicit reversible mapping to the canonical SemVer identity |
| Git release branch | permanent `release/0.2.0` |
| Git tag | annotated `0.2.0-pre-alpha.2` on the approved release commit |
| OCI image | immutable digest plus `0.2.0-pre-alpha.2` convenience tag |
| API contract | OpenAPI `info.version: 0.2.0-pre-alpha.2` |
| Pipeline manifest | release ID, Git commit, image digest, schema/corpus/template/model/policy digests |
| GitHub release | prerelease, only after remote/release authority; attach checksums, SBOM and notes |

Because `main` is defined as a production ledger and Pre-Alpha is not production,
the Pre-Alpha tag remains on the permanent release branch unless an accountable
repository authority records a stricter branch-policy adaptation. The plan does
not merge a Pre-Alpha candidate into `main` by implication.

## 5. Product vision slice and release goals

### Primary goals

- Close UAT-15 with governed run/artifact enumeration and CSV download.
- Make UAT-14 pass through an accountable human-review path, not an invented
  automatic identity.
- Replace fixed sample location values with validated collection context.
- Move the HTTP user journey from a 140-second synchronous request to a durable
  asynchronous job contract with status, cancellation and replay.
- Create a leakage-aware, rights-bound fixture and metric baseline sufficient
  to expose quality gaps honestly to authorized Pre-Alpha evaluators.
- Normalize version, release, SBOM, provenance, recovery and communication
  evidence for one reproducible local Pre-Alpha release.

### Secondary goals

- Introduce provider/validator interfaces for symbol zones and implement a
  bounded baseline for the set, rarity and energy symbol families represented
  by approved fixtures.
- Add template, zone, extraction and candidate-recall scorecards for the claimed
  Pre-Alpha fixture strata.
- Preserve the modular-monolith core and adapter parity; do not introduce
  distributed microservices or a vector database.

## 6. Scope

### In scope

| Epic | Capability effect | Architecture binding |
|---|---|---|
| EP-00 Release identity and contract normalization | one version truth source, migration and release evidence | CAP-001, CAP-015 |
| EP-01 Durable analysis jobs and collection context | async submit/status/cancel/replay; validated location metadata | CAP-001, CAP-013, CAP-015 |
| EP-02 Run and artifact delivery | authorized enumeration, streaming download and content metadata | CAP-002, CAP-015 |
| EP-03 Review, supersession and effective inventory | resolve ambiguous proposals with attributable append-only assertions | CAP-013 |
| EP-04 Evaluation foundation and semantic evidence uplift | adjudicated fixture registry, initial metrics, symbol-provider baseline | CAP-006–010, CAP-014 |
| EP-05 Pre-Alpha release hardening and evidence | parity, threat controls, recovery, load, SBOM, provenance, UAT | CAP-015 |

### Explicitly out of scope

- production deployment or shared public hosting;
- automatic card/printing confirmation;
- a claim that the detector is robust or meticulous;
- grading, condition, authenticity, pricing or valuation;
- complete historical template taxonomy or all languages;
- media acquisition without an approved rights manifest;
- distributed services, Kubernetes or external queue infrastructure;
- Pre-Alpha-to-Alpha, Alpha-to-Beta or General Availability promotion.

## 7. Actors and use-case outcomes

| Actor | Use-case outcome in `0.2.0-pre-alpha.2` |
|---|---|
| Collector/operator | submit a page with collection/binder/page context and receive a durable job ID |
| Collector/operator | retrieve proposal CSV, summary, manifest and permitted evidence by API |
| Reviewer | inspect an ambiguous pocket and append an attributable disposition |
| Reviewer/data steward | supersede a prior assertion without deleting historical evidence |
| Evaluator | register rights-qualified truth fixtures and run repeatable component/e2e scorecards |
| Developer/maintainer | run Python, CLI and HTTP contract suites from one shared application core |
| Operator/SRE | start, stop, resume, cancel, inspect and recover local jobs with bounded resources |
| Security/QA/release authorities | review exact evidence and return independent dispositions for the candidate digest |

The detailed use cases and user stories are in
[`RELEASE-BACKLOG-AND-TRACEABILITY.md`](RELEASE-BACKLOG-AND-TRACEABILITY.md).

## 8. Target architecture increment

The release preserves the local-first modular monolith and adds four bounded
application services around the existing analysis core:

1. **Job service** — persists `AnalysisJob`, validates context, seals the input,
   invokes the existing pipeline through a worker port and appends state.
2. **Artifact service** — resolves only manifest-listed artifacts beneath the
   authorized run store, enforces media type and path controls, and streams by
   immutable identity.
3. **Review service** — builds a read model from existing evidence, validates a
   reviewer disposition and appends `HumanReviewDisposition` and
   `SupersedingAssertion` records.
4. **Inventory projector** — deterministically resolves the latest effective
   assertion for stable collection/binder/page/pocket locations and emits
   non-overwriting CSV/JSONL/SQLite projections.

An evaluation adapter registers fixtures and calculates versioned metrics. It
must not mutate runtime evidence or adopt thresholds automatically.

## 9. External and internal contracts

### Target HTTP surface

| Method/path | Required behavior |
|---|---|
| `POST /v1/analysis-jobs` | multipart image plus validated context; return `202`, job ID and status link |
| `GET /v1/analysis-jobs/{job_id}` | job/run state, progress, manifest identity, terminal links |
| `POST /v1/analysis-jobs/{job_id}:cancel` | idempotent cancel request; preserve completed evidence |
| `GET /v1/runs/{run_id}` | bounded run summary and permitted links |
| `GET /v1/runs/{run_id}/artifacts` | enumerate manifest-listed downloadable artifacts |
| `GET /v1/runs/{run_id}/artifacts/{artifact_id}` | stream exact permitted artifact with digest and media type |
| `GET /v1/reviews?state=required` | paginate review-required pockets |
| `GET /v1/reviews/{review_id}` | evidence read model and version token |
| `POST /v1/reviews/{review_id}/dispositions` | append actor/reason/scope/action using optimistic concurrency |
| `GET /v1/inventories/{collection_id}` | latest effective, evidence-linked inventory projection |

The existing synchronous `POST /v1/pages/analyze` remains temporarily available
as an explicitly deprecated local compatibility adapter. It must call the same
job/application service and may be removed before Beta after a recorded contract
decision.

### Context contract

Required fields: `collection_id`, `binder_id`, `page_id` or server-generated
page identity, source capture time when known, and caller idempotency key.
Identifiers use a documented character/length grammar, are treated as opaque,
and never become filesystem paths. Context is immutable for a run; correction
creates a superseding location assertion or successor run.

### Review contract

Supported actions: select candidate identity, reject all candidates, correct a
field, request recapture, or leave unresolved. Identity and printing decisions
remain separate. Every accepted action requires actor identity, authority scope,
reason, evidence version token and expected prior effective assertion.

## 10. Data and migration plan

New versioned objects include `AnalysisJob`, `JobTransition`, `CollectionRef`,
`BinderRef`, `PageLocation`, `ArtifactDescriptor`, `ReviewCase`,
`HumanReviewDisposition`, `SupersedingAssertion`, `EffectiveInventoryProjection`,
`GroundTruthFixture`, `Annotation`, `Adjudication`, `BenchmarkRun` and
`MetricResult`.

Migration principles:

- Existing evidence runs remain immutable and readable.
- A one-time importer may create context aliases for historical sample runs but
  must label them `MIGRATED_SAMPLE_CONTEXT`; it cannot manufacture user intent.
- Database migrations are forward-only during release preparation and must have a
  rehearsed rollback/read-compatibility plan.
- Schema/API compatibility fixtures bind old UAT evidence to the new readers.
- Inventory projection version increments whenever resolution semantics change.

## 11. Security, privacy and rights controls

- Keep the default API bound to loopback; network exposure is out of scope.
- Use a local authenticated reviewer/operator identity mechanism before review
  actions are accepted; anonymous writes are prohibited.
- Authorize artifact access by run and artifact manifest, never caller paths.
- Validate magic type, decoder bounds, length, pagination, range requests and
  content disposition.
- Keep OCR/model/corpus/media acquisition outside the offline analysis path.
- Never return absolute host paths or untrusted OCR text in control/log fields.
- Preserve source and evidence retention settings explicitly; default to local
  restricted retention until DR-006 is decided.
- Permit reference images/fixtures only when rights and provenance state allow
  the exact use.
- Produce dependency/license inventory, SBOM, vulnerability findings and secret
  scan for the exact image digest.

## 12. Evaluation and acceptance strategy

### Quality tiers

1. Contract/unit/property tests for identifiers, state transitions, schemas,
   path controls, supersession and projection.
2. Component tests for jobs, artifacts, review, symbol providers and metrics.
3. Python/CLI/HTTP parity and migration tests.
4. End-to-end fixture flows: submit → job → evidence → review → inventory.
5. Adversarial tests for corrupt/oversized files, traversal, stale versions,
   conflicting review, cancellation and worker interruption.
6. Container tests for non-root/read-only behavior, restart, capacity and
   deterministic replay.
7. UAT against the supplied sample plus at least the approved Pre-Alpha 2 fixture
   matrix.

### Required UAT outcomes

- Preserve UAT-01 through UAT-13.
- UAT-15 successor passes: a user retrieves `inventory.csv` over HTTP and its
  digest matches the run manifest.
- UAT-14 successor passes only through an attributable review on the approved
  sample truth: every finalized row links to a review assertion; unresolved
  rows remain proposal-only.
- Context supplied in the request appears identically in CSV/JSONL/SQLite.
- Primary submit returns `202` within the accepted local admission budget; long
  analysis occurs in worker state, not the request thread.
- Restart/cancel/replay leave no duplicate effective assertions or corrupt
  artifacts.
- Initial template/zone/extraction/retrieval scorecards are generated by stratum
  with `EvidenceRequired` retained for unaccepted thresholds.

### Automatic-confirmation safety gate

`CONFIRMED_AUTOMATIC` remains prohibited in `0.2.0-pre-alpha.2`. Enabling it is not a
stretch goal. It requires a later release with a held-out false-confirmation
ceiling, calibration evidence and an explicit policy adoption decision.

## 13. Delivery waves and critical path

| Wave | Primary work | Entry | Exit evidence | Planning range |
|---|---|---|---|---:|
| R0 Govern and normalize | version truth, repository adaptation, owners, Pre-Alpha commitment, contract schemas | approved plan candidate | recorded product and architecture decisions | 1–2 weeks |
| R1 Preserve job truth | durable job store, context, worker port, status/cancel/replay | R0 | state/idempotency/interruption suites | 2–3 weeks |
| R2 Deliver artifacts | run/artifact API, streaming, path/auth controls | R1 | digest parity, negative and authorization tests | 1–2 weeks |
| R3 Resolve ambiguity | review read model/API, supersession, projection, minimal accessible local UI or CLI | R1–R2 | end-to-end reviewed inventory and conflict tests | 3–4 weeks |
| R4 Measure the system | fixture/adjudication foundation, scorecards, symbol-provider baseline | R0; rights-approved fixtures | leakage/provenance audit and reproducible baseline | 3–4 weeks |
| R5 Harden and release | parity, recovery, load, threat review, SBOM, UAT, notes, exact-digest gate | R2–R4 | candidate evidence packet and independent dispositions | 2–3 weeks |

With 4–5 suitably skilled contributors, the planning range is 10–14 calendar
weeks after R0 decisions and fixture availability; the sum is not a commitment.
Missing role acceptance, rights-qualified fixtures or remote credentials can
extend or stop only the affected gate.

Critical path:

`version/contracts → durable jobs → artifact delivery → review/supersession →`
`effective inventory → Pre-Alpha 2 UAT → independent release decision`

Evaluation fixture work proceeds in parallel after R0 and joins before Pre-Alpha
UAT. Template/zone/extractor changes feed measured scorecards and may not
silently revise review or decision semantics.

## 14. Roles, decisions and gates

| Gate | Required actual dispositions | Exit condition |
|---|---|---|
| RG-0 Scope/version | Product Owner, Tech Lead | release scope, `0.2.0-pre-alpha.2` target, syntax adaptation and compatibility boundary accepted |
| RG-1 Contracts/data | Tech Lead, Data Steward, Security | job/context/artifact/review schemas and migration plan accepted |
| RG-2 Truth/rights | Evaluation Owner, Data Steward | fixture protocol, rights and leakage controls accepted |
| RG-3 Feature complete | Product, Engineering, QA | all required stories meet evidence-bearing DoD |
| RG-4 Candidate qualified | QA/Eval, Security/Platform, Licensing | tests, benchmark baseline, threat/recovery/load and SBOM dispositions returned |
| RG-5 Pre-Alpha truthfulness | Product/CIO plus evaluation owner | experimental commitment boundary, audience restrictions and feedback path recorded; no Alpha claim |
| RG-6 Release | Release Authority | exact commit/image digest approved for tag/publication |

Roles remain `TO_BE_APPOINTED` until real actors accept them. A document listing
a role does not satisfy a gate.

## 15. Git, CI and release procedure

1. Continue scoped development on feature branches; preserve unsquashed commit
   history.
2. Establish `release/0.2.0` only when RG-0 fixes the release scope.
3. Merge accepted feature branches into the release branch with traceable
   non-squash merges.
4. Run format/lint/type/secret/license, unit/property, integration/migration,
   architecture, container and docs/manifest checks.
5. Build the candidate once; bind Git commit, OCI digest, SBOM, provenance,
   corpus, template, model, policy and schema versions.
6. Deploy that exact digest to the local Pre-Alpha UAT surface and execute UAT,
   recovery, load and security checks.
7. Collect actual RG-4 through RG-6 dispositions. Do not proxy-author them.
8. During release preparation only, update product/version surfaces, changelog,
   release notes and migration guide together.
9. Annotate `0.2.0-pre-alpha.2` on the approved release commit; sign when the
   approved signing mechanism is available.
10. Push the permanent release branch and tag, then create a GitHub prerelease
    with checksums and evidence links. Remote publication requires resolved
    credentials and authority.
11. Preserve the release branch. Do not merge to the production-only `main`
    without an explicit repository-authority decision.

## 16. Release evidence packet

The candidate packet must include:

- exact source commit, clean-tree record and permanent release branch;
- annotated tag and version-consistency report;
- OCI digest, platform matrix, SBOM, provenance and vulnerability report;
- dependency/license and model/corpus/media rights registers;
- schemas, migration plan/results and compatibility report;
- API contract and Python/CLI/HTTP parity results;
- unit/property/component/integration/e2e/adversarial results;
- UAT result with artifact-download and reviewed-inventory evidence;
- evaluation fixture manifest, leakage audit and qualified scorecards;
- performance/resource/cancellation/recovery and backup/restore evidence;
- threat-control and secret-scan results;
- known defects, risk acceptance, rollback target and release notes;
- actual participating role dispositions and Pre-Alpha truthfulness record.

## 17. Rollback and failure handling

The release is local-first and append-only. Rollback selects the prior signed or
sealed application/image and compatible read model; it never deletes evidence
created by the Pre-Alpha candidate. New projections may be recomputed from preserved
assertions.

Required rehearsals:

- worker crash between artifact write and transition append;
- API restart during running job;
- cancel during OCR and during projection;
- corrupt artifact and missing manifest member;
- stale optimistic-concurrency token and conflicting review;
- failed forward migration and compatible reader restoration;
- resource exhaustion and capacity rejection with `Retry-After`.

A failed feature or gate returns the affected work to the nearest valid
checkpoint. It does not authorize data repair, release bypass or global history
rewrite.

## 18. Evidence-bearing definition of done

A story is complete only when:

- implementation and versioned contracts exist;
- required positive, negative, migration and failure tests pass;
- evidence is bound to the exact commit/configuration/environment;
- documentation, API schema and runbooks agree with behavior;
- security/privacy/rights constraints applicable to the story pass;
- the accountable owner records the required disposition;
- no unresolved exception is hidden by a completion label.

The release is complete only when every required story and RG-0 through RG-6
passes for the exact candidate, the tag and prerelease actually exist, the
release assets verify, and the communicated Pre-Alpha commitment boundary matches
reality.

## 19. Risks and stop conditions

| Risk/stop | Required response |
|---|---|
| No accountable role or release authority | stop only the affected gate; continue reversible engineering |
| Version surfaces or governance adaptation disagree | stop release preparation; reconcile every surface to `0.2.0-pre-alpha.2` and preserve Pre-Alpha classification |
| Fixture/media rights unresolved | exclude those assets/strata; no silent acquisition |
| Evidence or manifest integrity failure | suspend affected candidate, preserve counterevidence, rebuild |
| False automatic confirmation | severity-1 release blocker; automatic path remains disabled |
| Review cannot be authenticated/attributed | do not permit effective inventory mutation |
| Migration lacks rollback/read compatibility | stop candidate promotion |
| Critical/high security finding unaccepted | stop RG-4/RG-6 |
| Remote credential/permission absent | local candidate may remain sealed; publication is blocked |
| Scope expansion into production hosting or pricing/grading | require a new mandate and architecture review |

## 20. Post-release roadmap boundary

After `0.2.0-pre-alpha.2`, later Pre-Alpha or Alpha releases may broaden template and
language coverage, typed symbol/printing extraction, candidate recall,
calibration, UI quality and operating envelopes. Beta is not eligible until
controlled external-validation processes, compatibility expectations, selected
partners and feedback governance are actually established.

The full “robust and meticulous” vision remains governed by the complete
CAP-001–015 and WP-001–052 evidence set. This release is a deliberate product
capability increment, not a substitute for that production roadmap.

## 21. Plan disposition and nonclaims

**Plan disposition:** `COMPLETE_WITH_QUALIFIED_RESULTS`.

This artifact supplies a product/release strategy, capability slice, actor/use-
case model, backlog, dependency order, acceptance contract and release gate
design. It does not establish that any feature was implemented, any independent
review occurred, release authority was granted, or `0.2.0-pre-alpha.2` was released.
