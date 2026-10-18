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
authorized. Tagging, remote publication, GitHub release creation, lifecycle
promotion, and production merge are not authorized by this adaptation.
