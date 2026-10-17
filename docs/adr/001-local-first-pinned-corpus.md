# ADR-001: Local-first pinned corpus

Status: Accepted for the vertical slice.

Use a commit-pinned local TCGdex snapshot compiled into read-only SQLite. This
makes candidate generation reproducible and removes runtime network dependence.
Raw source payloads and hashes remain available for audit. The tradeoff is that
upstream defects and missing media are preserved and must be qualified rather
than silently repaired.
