from __future__ import annotations

from pathlib import Path
from typing import Any

from .ocr import EasyOCRProvider, NullOCRProvider, OCRProvider
from .pipeline import analyze_page
from .util import project_root


def build_ocr_provider(
    mode: str = "easyocr",
    *,
    model_directory: Path | None = None,
    download_enabled: bool = False,
) -> OCRProvider:
    """Build an OCR adapter without coupling callers to provider details."""
    if mode == "none":
        return NullOCRProvider()
    if mode != "easyocr":
        raise ValueError(f"unsupported OCR mode: {mode}")
    directory = model_directory or project_root() / ".models" / "easyocr"
    return EasyOCRProvider(directory, download_enabled=download_enabled)


def analyze_page_request(
    image_path: Path,
    database_path: Path,
    template_root: Path,
    output_parent: Path,
    *,
    ocr_mode: str = "easyocr",
    download_ocr_models: bool = False,
    model_directory: Path | None = None,
) -> dict[str, Any]:
    """Execute page analysis for CLI, HTTP, or an importing Python process."""
    provider = build_ocr_provider(
        ocr_mode,
        model_directory=model_directory,
        download_enabled=download_ocr_models,
    )
    return analyze_page(
        image_path,
        database_path,
        template_root,
        output_parent,
        provider,
    )
