from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


class TemplateError(ValueError):
    pass


class TemplateRegistry:
    def __init__(self, root: Path):
        self.root = root
        self._raw: dict[str, dict[str, Any]] = {}
        for path in sorted(root.rglob("*.yaml")):
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or "template_id" not in payload:
                raise TemplateError(f"invalid template: {path}")
            template_id = payload["template_id"]
            if template_id in self._raw:
                raise TemplateError(f"duplicate template_id: {template_id}")
            payload["_source_path"] = str(path)
            self._raw[template_id] = payload

    def ids(self) -> list[str]:
        return sorted(self._raw)

    def resolve(self, template_id: str) -> dict[str, Any]:
        return self._resolve(template_id, [])

    def _resolve(self, template_id: str, stack: list[str]) -> dict[str, Any]:
        if template_id not in self._raw:
            raise TemplateError(f"unknown template: {template_id}")
        if template_id in stack:
            raise TemplateError(f"template inheritance cycle: {' -> '.join(stack + [template_id])}")
        current = copy.deepcopy(self._raw[template_id])
        parent_id = current.get("parent_template_id")
        if not parent_id:
            return current
        parent = self._resolve(parent_id, stack + [template_id])
        merged = _deep_merge(parent, current)
        merged["resolved_lineage"] = parent.get("resolved_lineage", [parent_id]) + [template_id]
        return merged

    def validate(self) -> list[str]:
        findings: list[str] = []
        required_zone_fields = {"rect", "data_type", "extractor"}
        for template_id in self.ids():
            template = self.resolve(template_id)
            for zone_id, zone in template.get("zones", {}).items():
                missing = required_zone_fields - set(zone)
                if missing:
                    findings.append(f"{template_id}.{zone_id}: missing {sorted(missing)}")
                    continue
                rect = zone["rect"]
                if len(rect) != 4 or any(not 0 <= float(v) <= 1 for v in rect):
                    findings.append(f"{template_id}.{zone_id}: rect outside normalized bounds")
                if float(rect[0]) + float(rect[2]) > 1 or float(rect[1]) + float(rect[3]) > 1:
                    findings.append(f"{template_id}.{zone_id}: rect exceeds card boundary")
        return findings


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def crop_zone(image, zone: dict[str, Any]):
    height, width = image.shape[:2]
    x, y, w, h = (float(value) for value in zone["rect"])
    x0, y0 = max(0, round(x * width)), max(0, round(y * height))
    x1, y1 = min(width, round((x + w) * width)), min(height, round((y + h) * height))
    return image[y0:y1, x0:x1], [x0, y0, x1, y1]
