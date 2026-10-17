from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import imagehash
from PIL import Image


def compare_images(observed_path: Path, reference_path: Path) -> dict[str, Any]:
    observed_hash = imagehash.phash(Image.open(observed_path).convert("RGB"))
    reference_hash = imagehash.phash(Image.open(reference_path).convert("RGB"))
    phash_similarity = max(0.0, 1 - (observed_hash - reference_hash) / 64)
    observed = cv2.imread(str(observed_path), cv2.IMREAD_GRAYSCALE)
    reference = cv2.imread(str(reference_path), cv2.IMREAD_GRAYSCALE)
    if observed is None or reference is None:
        raise ValueError("image comparison input could not be decoded")
    observed = cv2.resize(observed, (630, 880))
    reference = cv2.resize(reference, (630, 880))
    orb = cv2.ORB_create(nfeatures=800)
    _, observed_descriptors = orb.detectAndCompute(observed, None)
    _, reference_descriptors = orb.detectAndCompute(reference, None)
    local_similarity = 0.0
    match_count = 0
    if observed_descriptors is not None and reference_descriptors is not None:
        matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(
            observed_descriptors, reference_descriptors
        )
        good = [match for match in matches if match.distance <= 55]
        match_count = len(good)
        # Normalize by the available evidence, not by an arbitrary absolute
        # feature count. Sparse but identical card art should still score as
        # identical; the fused decision policy separately guards against using
        # this score as proof of an exact printing.
        available = min(len(observed_descriptors), len(reference_descriptors))
        local_similarity = min(1.0, match_count / available) if available else 0.0
    score = 0.55 * phash_similarity + 0.45 * local_similarity
    return {
        "method": "phash64+orb-v1",
        "phash_similarity": round(phash_similarity, 6),
        "orb_good_match_count": match_count,
        "orb_similarity": round(local_similarity, 6),
        "score": round(score, 6),
        "printing_identity_sufficient": False,
        "nonclaim": "art/full-face similarity alone cannot establish an exact printing",
    }
