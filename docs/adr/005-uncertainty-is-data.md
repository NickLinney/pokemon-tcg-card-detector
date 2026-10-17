# ADR-005: Uncertainty is data

Status: Accepted.

`UNKNOWN`, `AMBIGUOUS`, `CONFLICTING`, and `INSUFFICIENT_EVIDENCE` are durable
states, not exceptions to hide. Inventory exports carry state, confidence, and
review requirement. This reduces automated completion but prevents unsupported
identities from becoming collection facts.
