from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Protocol

import cv2

from .util import japanese_character_fraction, normalize_text


class OCRProvider(Protocol):
    provider_id: str

    def read(self, image, *, allowlist: str | None = None) -> dict[str, Any]: ...


class EasyOCRProvider:
    provider_id = "easyocr:1.7.2:ja+en"

    def __init__(self, model_directory: Path, download_enabled: bool = False):
        import easyocr

        model_directory.mkdir(parents=True, exist_ok=True)
        self.reader = easyocr.Reader(
            ["ja", "en"],
            gpu=False,
            model_storage_directory=str(model_directory),
            user_network_directory=str(model_directory / "user_network"),
            download_enabled=download_enabled,
            verbose=False,
        )

    def read(self, image, *, allowlist: str | None = None) -> dict[str, Any]:
        if image.size == 0:
            return _empty_result(self.provider_id, "empty_zone")
        enlarged = cv2.resize(image, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
        kwargs: dict[str, Any] = {
            "detail": 1,
            "paragraph": False,
            "mag_ratio": 1.5,
            "contrast_ths": 0.05,
            "adjust_contrast": 0.7,
        }
        if allowlist:
            kwargs["allowlist"] = allowlist
        rows = self.reader.readtext(enlarged, **kwargs)
        alternatives = []
        for box, text, confidence in rows:
            alternatives.append(
                {
                    "text": text,
                    "confidence": round(float(confidence), 6),
                    "geometry": [[round(float(x / 2.5), 2), round(float(y / 2.5), 2)] for x, y in box],
                }
            )
        alternatives.sort(key=lambda item: item["geometry"][0][0] if item["geometry"] else 0)
        raw_text = " ".join(item["text"] for item in alternatives).strip()
        confidence = (
            sum(item["confidence"] for item in alternatives) / len(alternatives) if alternatives else 0.0
        )
        return {
            "provider": self.provider_id,
            "raw_text": raw_text,
            "normalized_text": normalize_text(raw_text),
            "confidence": round(confidence, 6),
            "alternatives": alternatives,
            "error": None,
        }


class NullOCRProvider:
    provider_id = "none"

    def read(self, image, *, allowlist: str | None = None) -> dict[str, Any]:
        return _empty_result(self.provider_id, "ocr_provider_unavailable")


def _empty_result(provider: str, error: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "raw_text": "",
        "normalized_text": None,
        "confidence": 0.0,
        "alternatives": [],
        "error": error,
    }


def parse_hp(result: dict[str, Any]) -> int | None:
    text = result.get("raw_text", "")
    hp_match = re.search(r"H\s*P?\s*([0-9OSoC]{2,3})", text, re.I)
    if hp_match:
        normalized = hp_match.group(1).upper().translate(str.maketrans({"O": "0", "S": "5", "C": "0"}))
        value = int(normalized)
        if 10 <= value <= 400 and value % 10 == 0:
            return value
    values = [int(value) for value in re.findall(r"\d{2,3}", text)]
    plausible = [value for value in values if 10 <= value <= 400 and value % 10 == 0]
    return plausible[0] if plausible else None


def parse_collector_number(result: dict[str, Any]) -> dict[str, str] | None:
    text = result.get("raw_text", "")
    match = re.search(r"(?<!\d)(\d{1,3})\s*[/／]\s*(\d{1,3})(?!\d)", text)
    if match:
        return {"local_id": match.group(1).zfill(3), "set_count": match.group(2)}
    single = re.search(r"(?<!\d)(\d{3})(?!\d)", text)
    return {"local_id": single.group(1)} if single else None


def classify_script(result: dict[str, Any]) -> dict[str, Any]:
    fraction = japanese_character_fraction(result.get("raw_text", ""))
    return {
        "script": "Japanese" if fraction >= 0.2 else "Unknown",
        "japanese_character_fraction": round(fraction, 6),
        "basis": "OCR Unicode ranges",
    }
