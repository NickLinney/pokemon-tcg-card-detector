# Versioning

This repository follows Semantic Versioning and the NickLinneyDev early-life
cycle convention with a project-specific Pre-Alpha adaptation authorized for
this product line.

- Pre-alpha releases: `0.MINOR.PATCH-pre-alpha.N`
- Alpha: `0.MINOR.0-alpha`
- Beta: `0.MINOR.0-beta`
- Release candidate: `MAJOR.MINOR.PATCH-rc.N`
- Stable: `MAJOR.MINOR.PATCH`

The numeric core and lifecycle are independent: `0.2.0-pre-alpha.2` is the
second pre-1.0 minor capability increment and remains Pre-Alpha sequence 2. It
does not imply Alpha maturity. Python distribution metadata maps this identity
reversibly to `0.2.0.dev2` because PEP 440 does not admit `pre-alpha`.

Version changes occur only during an explicit release preparation event and
must be accompanied by release notes, changelog updates, and an annotated tag.
The current identity is an unreleased development target until every release
gate and actual Release Authority disposition is present.
