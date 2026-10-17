# ADR-002: Separate reference, observation, and decision truth

Status: Accepted.

Reference records, measured observations, and inferred decisions use distinct
schemas and fields. A likely candidate cannot rewrite OCR or source metadata.
This adds serialization detail but prevents provenance loss and makes later
reprocessing possible.
