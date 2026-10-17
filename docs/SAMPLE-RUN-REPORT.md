# Commissioned Sample Run Report

## Run identity

- source SHA-256: `5cc94e4d838f0bd7e95b7d141a62d457000aa97b97df00c1bd2eed2188938205`
- run: `../.local/runs/run-5cc94e4d838f-3`
- summary SHA-256: `66d4d3eb98473305993fd563f8654245dacc392d7fa2270d3aa32cde1f430d28`
- inventory JSONL SHA-256: `443984498dd1be27cb29baff478bd93258dd159e3d75c25ac383dd19ad8ded75`
- inventory CSV SHA-256: `9ddd8b5f4ee5aba24610ca1699e39b825b1a012170d010a26d08910c2db2f72c`
- inventory SQLite SHA-256: `f76a885717ce0fa740e8eca7cee6a0a10700f1ea7d34a7eb93a231d8a17ae960`

## Measured outcome

- page dimensions: 1152x1536;
- cards segmented: 9/9;
- pocket ordering: `[1,2,3,4,5,6,7,8,9]` row-major;
- normalized crops: 9;
- evidence packages: 9;
- decision counts: `AMBIGUOUS=9`;
- unsupported confirmations: 0;
- reference-image comparisons on sample: 0 (source unavailable).

The final crop geometry includes all nine card faces and preserves polygons back
to the immutable page. OCR recovered useful Japanese title fragments in several
pockets and HP 60/50 values in six pockets. Candidate retrieval placed plausible
VS1 records at or near the top for several cards, but no result met the evidence,
margin, source-quality, and contradiction gates required for confirmation.

The all-ambiguous outcome is not a successful identity benchmark. It is a
successful safety result: imperfect OCR and known upstream-name defects were not
converted into false inventory facts. A curated, legally usable VS1 reference
image set and reviewed ground truth are the next evidence needed for accuracy
measurement and calibration.
