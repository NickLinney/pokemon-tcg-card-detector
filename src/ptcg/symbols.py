from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import cv2
import numpy as np


class SymbolProvider(Protocol):
    provider_id: str

    def extract(
        self,
        image: np.ndarray,
        *,
        zone_id: str,
        template_id: str,
    ) -> dict[str, Any]: ...


class UnsupportedSymbolProvider:
    provider_id = "symbol:unsupported-v1"

    def extract(
        self,
        image: np.ndarray,
        *,
        zone_id: str,
        template_id: str,
    ) -> dict[str, Any]:
        return {
            "state": "UNSUPPORTED",
            "provider": self.provider_id,
            "typed_value": None,
            "uncertainty": "No rights-qualified prototype registry is configured.",
            "alternatives": [],
        }


@dataclass(frozen=True)
class PrototypeSymbolProvider:
    """Bounded perceptual-hash baseline for approved template strata."""

    prototypes: dict[str, dict[str, np.ndarray]]
    approved_template_prefixes: tuple[str, ...]
    maximum_hamming_fraction: float = 0.20
    provider_id: str = "symbol:approved-prototype-ahash-v1"

    def extract(
        self,
        image: np.ndarray,
        *,
        zone_id: str,
        template_id: str,
    ) -> dict[str, Any]:
        family = _symbol_family(zone_id)
        if family is None or family not in self.prototypes:
            return self._unsupported("zone family is outside the configured baseline")
        if not any(template_id.startswith(prefix) for prefix in self.approved_template_prefixes):
            return self._unsupported("template stratum is outside approved fixture coverage")
        observed = _average_hash(image)
        ranked = []
        for label, prototype in self.prototypes[family].items():
            expected = _average_hash(prototype)
            distance = int(np.count_nonzero(observed != expected))
            ranked.append(
                {
                    "label": label,
                    "hamming_fraction": distance / observed.size,
                }
            )
        ranked.sort(key=lambda item: (item["hamming_fraction"], item["label"]))
        if not ranked or ranked[0]["hamming_fraction"] > self.maximum_hamming_fraction:
            return {
                "state": "NO_SIGNAL",
                "provider": self.provider_id,
                "typed_value": None,
                "uncertainty": "No approved prototype met the bounded distance threshold.",
                "alternatives": ranked[:3],
            }
        return {
            "state": "SUCCEEDED",
            "provider": self.provider_id,
            "typed_value": {
                "symbol_family": family,
                "label": ranked[0]["label"],
            },
            "uncertainty": "Uncalibrated prototype distance; fixture-bound baseline only.",
            "alternatives": ranked[:3],
        }

    def _unsupported(self, reason: str) -> dict[str, Any]:
        return {
            "state": "UNSUPPORTED",
            "provider": self.provider_id,
            "typed_value": None,
            "uncertainty": reason,
            "alternatives": [],
        }


def _symbol_family(zone_id: str) -> str | None:
    lowered = zone_id.casefold()
    if "set_symbol" in lowered or lowered == "set":
        return "set"
    if "rarity" in lowered:
        return "rarity"
    if "energy" in lowered or "cost" in lowered:
        return "energy"
    return None


def _average_hash(image: np.ndarray) -> np.ndarray:
    if image.size == 0:
        return np.zeros((8, 8), dtype=bool)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    resized = cv2.resize(gray, (8, 8), interpolation=cv2.INTER_AREA)
    return resized >= float(resized.mean())
