"""Canonical product identity for the current governed development line."""

CANONICAL_VERSION = "0.2.0-pre-alpha.2"
PYTHON_DISTRIBUTION_VERSION = "0.2.0.dev2"
LIFECYCLE = "PRE_ALPHA"
RELEASED = False


def version_metadata() -> dict[str, str | bool]:
    """Return adapter-neutral version metadata without implying a release."""
    return {
        "canonical_version": CANONICAL_VERSION,
        "python_distribution_version": PYTHON_DISTRIBUTION_VERSION,
        "lifecycle": LIFECYCLE,
        "released": RELEASED,
    }
