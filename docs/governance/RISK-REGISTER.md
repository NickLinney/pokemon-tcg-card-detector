# Risk and Unresolved-State Register

| ID | State | Risk / unresolved condition | Current control |
|---|---|---|---|
| R-001 | Open | Supplied SSAC ZIP is a Mermaid model, not the named source package. | Record discrepancy; bind to exact matching local source-package SHA-256. |
| R-002 | Open | TCGdex metadata is MIT, but Pokémon imagery/media rights are separate and not established as FLOSS. | Keep media out of Git; record provenance and rights as unknown/restricted. |
| R-003 | Open | TCGdex VS1 Japanese names contain mixed English and apparent mistranslations. | Preserve raw source; use multiple independent fields and contradictions. |
| R-004 | Open | A single binder page cannot establish general accuracy or calibration. | Report fixture-only metrics and keep automatic thresholds conservative. |
| R-005 | Open | Sleeve glare, skew, and low text resolution may defeat OCR. | Record quality and raw OCR; allow insufficient/ambiguous decisions. |
| R-006 | Open | OCR model/data licensing may differ from EasyOCR code licensing. | Record code/model separately; do not redistribute downloaded weights. |
| R-007 | Open | Required independent release/security/QA acceptance has not occurred. | Keep lifecycle experimental/unreleased; do not simulate approval. |

