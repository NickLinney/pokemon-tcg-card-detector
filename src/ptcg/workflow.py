from __future__ import annotations

import re
from datetime import datetime
from typing import Any


CONTEXT_SCHEMA_VERSION = "collection-context-v1"
OPAQUE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def validate_collection_context(value: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize immutable collection location context."""
    context = {
        "schema_version": CONTEXT_SCHEMA_VERSION,
        "collection_id": value.get("collection_id"),
        "binder_id": value.get("binder_id"),
        "page_id": value.get("page_id"),
        "source_captured_at": value.get("source_captured_at"),
    }
    for field in ("collection_id", "binder_id", "page_id"):
        candidate = context[field]
        if not isinstance(candidate, str) or not OPAQUE_IDENTIFIER.fullmatch(candidate):
            raise ValueError(
                f"{field} must be 1-128 opaque ASCII letters, digits, '.', '_', ':', or '-'"
            )
    captured = context["source_captured_at"]
    if captured not in (None, ""):
        if not isinstance(captured, str):
            raise ValueError("source_captured_at must be an ISO 8601 string")
        try:
            datetime.fromisoformat(captured.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("source_captured_at must be an ISO 8601 date-time") from exc
    else:
        context["source_captured_at"] = None
    return context


def default_sample_context() -> dict[str, Any]:
    return validate_collection_context(
        {"collection_id": "sample", "binder_id": "sample", "page_id": "page-1"}
    )


def location_id(context: dict[str, Any], pocket_index: int) -> str:
    return (
        f"{context['collection_id']}:{context['binder_id']}:"
        f"{context['page_id']}:pocket-{pocket_index:02d}"
    )
