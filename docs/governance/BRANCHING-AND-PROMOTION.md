# Branching and Promotion Adaptation

Status: **adopted for the `0.2.0-pre-alpha.2` development line; release not authorized**

This repository uses the project-specific delivery path required by the robust
architecture plan and the Commissioner. It adapts the inherited generic
Pre-Alpha guidance that would otherwise merge directly to `main`.

## Branch roles

- `feature/*` contains one bounded feature or planning change. A feature is
  committed and verified independently.
- `dev` is the non-squash integration ledger for accepted feature commits.
- `test` is advanced from an exact `dev` integration commit only after the
  repository verification suite passes for that commit.
- `staging` is advanced from the same tested history only for controlled local
  UAT, recovery, load, migration and security rehearsal.
- `release/0.2.0` is the retained Pre-Alpha release-candidate ledger. It may be
  prepared from the exact staged commit but is not a release by existence.
- `main` remains the production ledger and is not changed by a Pre-Alpha
  candidate without an explicit repository/release-authority decision.

Feature integration uses traceable non-squash merges. Promotion branches are
fast-forwarded only from the previously verified branch so code is not rebuilt
or silently changed between environments. A branch pointer, merge, test pass,
image, plan, or generated record does not substitute for the role dispositions
required by RG-0 through RG-6.

## Current authority boundary

Local feature development, verification, and branch construction are
authorized. The Commissioner's 2026-10-18 correction explicitly authorizes
remote publication of the preserved branch graph plus genuine pull-request,
review, merge, and environment-promotion records. Tagging, GitHub release
creation, lifecycle promotion beyond the retained Pre-Alpha candidate, and
production merge remain unauthorized.

## Deferred-resource completion rule

A required credential, service, actor, corpus, model, or other execution
resource may be deferred while safe local work continues, but its dependent
work item remains explicitly incomplete. Progress and completion reports must:

- identify the deferred resource and the exact blocked transition prominently;
- distinguish locally complete work from remote, reviewed, promoted, released,
  or otherwise externally realized work;
- retain an owner, next action, and completion condition for the blocked item;
- never infer that an unattempted or credential-blocked transition was waived;
- reconcile the deferred item through its substantive workflow when the
  resource becomes available rather than merely editing its status text.

For GitHub publication, local commits and branches do not satisfy remote
provenance. Completion requires verified remote refs and, where governance
requires review, actual pull-request and review objects bound to the exact
commits. A review by the implementing account is recorded as non-independent
and cannot satisfy an independent QA, security, licensing, or release gate.
