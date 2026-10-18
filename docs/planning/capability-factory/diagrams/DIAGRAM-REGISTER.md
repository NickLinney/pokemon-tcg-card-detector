# Diagram Register

Every required capability specification contains two embedded Mermaid diagrams:
a boundary/dependency view and a behavior or state view. That yields thirty
capability-level diagrams. The following standalone cross-capability diagrams
provide the packet-level views.

| ID | Diagram | Purpose |
|---|---|---|
| D-001 | `01-CAPABILITY-MAP.mmd` | Fifteen-capability system decomposition |
| D-002 | `02-ARCHITECTURE-CRITICAL-PATH.mmd` | Dependency-ordered construction path |
| D-003 | `03-TRUTH-AND-EVIDENCE-FLOW.mmd` | Reference/observation/decision truth boundaries |
| D-004 | `04-RUN-STATE-MACHINE.mmd` | Analysis-run lifecycle and qualified failure |
| D-005 | `05-CAPABILITY-FACTORY-EXECUTION.mmd` | S01–S14 factory execution and feedback |

Diagram status is `SOURCE_PRODUCED`. Mermaid source rendering in capable
Markdown viewers is expected. Renderer-level validation is a distinct check and
must not be inferred from source existence.
