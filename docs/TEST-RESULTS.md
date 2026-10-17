# Test Results

Executed 2026-10-17 in the pinned project-local Python 3.12 environment:

```text
............                                                             [100%]
12 passed in 1.74s
```

Coverage includes text normalization and write-boundary enforcement, template
inheritance and validation, TCGdex parsing and compiled-corpus integrity,
nine-pocket segmentation and reversible bounds, OCR typed parsing, ambiguous and
conflicting decision behavior, synthetic image similarity, and JSON Schema
validity. Evidence serialization is verified for Unicode round-trip fidelity and
non-overwriting output allocation.

During validation, the identical-image fixture exposed an ORB score calibration
defect. The implementation now normalizes good matches by the descriptors
actually available rather than by a fixed feature count. The suite passed after
that correction.

This is component and single-fixture evidence, not broad model accuracy,
security acceptance, or production qualification.
