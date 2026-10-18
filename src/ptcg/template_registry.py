from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from .util import canonical_json_sha256


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

    def candidate_ids(self) -> list[str]:
        """Return classification candidates, excluding the abstract card base."""
        return [template_id for template_id in self.ids() if template_id != "card.base.v1"]

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
            current["resolved_lineage"] = [template_id]
            current["zones"] = {
                zone_id: _compile_zone(zone_id, zone)
                for zone_id, zone in current.get("zones", {}).items()
            }
            return current
        parent = self._resolve(parent_id, stack + [template_id])
        for zone_id, override in current.get("zones", {}).items():
            inherited = parent.get("zones", {}).get(zone_id)
            if (
                inherited
                and "data_type" in override
                and override["data_type"] != inherited.get("data_type")
            ):
                raise TemplateError(
                    f"{template_id}.{zone_id}: child override changes data_type "
                    f"from {inherited.get('data_type')} to {override['data_type']}"
                )
        merged = _deep_merge(parent, current)
        merged["resolved_lineage"] = parent.get("resolved_lineage", [parent_id]) + [template_id]
        merged["zones"] = {
            zone_id: _compile_zone(zone_id, zone)
            for zone_id, zone in merged.get("zones", {}).items()
        }
        return merged

    def compiled_view(self) -> dict[str, Any]:
        templates = {template_id: self.resolve(template_id) for template_id in self.ids()}
        for template in templates.values():
            template.pop("_source_path", None)
        return {
            "schema_version": "template-registry-view-v1",
            "templates": templates,
            "coverage": self.coverage(),
        }

    def digest(self) -> str:
        return canonical_json_sha256(self.compiled_view())

    def coverage(self) -> dict[str, Any]:
        templates = [self.resolve(template_id) for template_id in self.ids()]
        zone_ids = sorted(
            {zone_id for template in templates for zone_id in template.get("zones", {})}
        )
        families: dict[str, list[str]] = {}
        for zone_id in zone_ids:
            family = _ZONE_FAMILIES.get(zone_id, "unclassified")
            families.setdefault(family, []).append(zone_id)
        return {
            "template_count": len(templates),
            "candidate_template_count": len(self.candidate_ids()),
            "semantic_zone_count": len(zone_ids),
            "anchor_ids": sorted(
                {anchor_id for template in templates for anchor_id in template.get("anchors", {})}
            ),
            "semantic_families": dict(sorted(families.items())),
            "classification_dimensions": sorted(
                {
                    key
                    for template in templates
                    for key in ("category", "language", "region", "era", "mechanic")
                    if template.get(key) is not None
                }
            ),
            "qualification": (
                "Registry coverage describes declared templates and zones; it is not runtime "
                "detection or benchmark evidence."
            ),
        }

    def validate(self) -> list[str]:
        findings: list[str] = []
        required_zone_fields = {"rect", "data_type", "extractor"}
        for template_id in self.ids():
            try:
                template = self.resolve(template_id)
            except TemplateError as exc:
                findings.append(str(exc))
                continue
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
                if zone.get("semantic_family") == "unclassified":
                    findings.append(f"{template_id}.{zone_id}: semantic family is unclassified")
                if zone.get("cardinality") not in {"one", "zero-or-one", "many"}:
                    findings.append(f"{template_id}.{zone_id}: invalid cardinality")
                anchor_id = zone.get("locator", {}).get("anchor")
                if anchor_id and anchor_id not in template.get("anchors", {}):
                    findings.append(
                        f"{template_id}.{zone_id}: locator references unknown anchor {anchor_id}"
                    )
            for anchor_id, anchor in template.get("anchors", {}).items():
                rect = anchor.get("rect")
                if not isinstance(rect, list) or len(rect) != 4:
                    findings.append(f"{template_id}.anchor.{anchor_id}: invalid rect")
                    continue
                if any(not 0 <= float(value) <= 1 for value in rect):
                    findings.append(f"{template_id}.anchor.{anchor_id}: rect outside bounds")
                if float(rect[0]) + float(rect[2]) > 1 or float(rect[1]) + float(rect[3]) > 1:
                    findings.append(f"{template_id}.anchor.{anchor_id}: rect exceeds card boundary")
            for relation in template.get("relationships", []):
                subject = relation.get("subject")
                object_id = relation.get("object")
                if subject not in template.get("zones", {}) or object_id not in template.get("zones", {}):
                    findings.append(
                        f"{template_id}: relationship references unknown zones {subject}, {object_id}"
                    )
        return findings


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


_ZONE_FAMILIES = {
    "title": "identity",
    "owner_mechanic": "identity",
    "classification": "classification",
    "hp": "vital_numeric",
    "damage": "vital_numeric",
    "attack_costs": "type_and_costs",
    "retreat": "type_and_costs",
    "abilities": "mechanics",
    "attacks": "mechanics",
    "weakness": "matchups",
    "resistance": "matchups",
    "set_symbol": "catalogue",
    "collector_number": "catalogue",
    "rarity": "catalogue",
    "regulation_edition_promo": "legality_era_printing",
    "illustrator": "attribution",
    "artwork": "artwork",
    "special_layout_markers": "special",
    "copyright_footer": "footer",
}


def _compile_zone(zone_id: str, zone: dict[str, Any]) -> dict[str, Any]:
    compiled = copy.deepcopy(zone)
    compiled.setdefault("semantic_id", f"zone:{zone_id}")
    compiled.setdefault("semantic_family", _ZONE_FAMILIES.get(zone_id, "unclassified"))
    compiled.setdefault("cardinality", "many" if zone_id in {"abilities", "attacks"} else "zero-or-one")
    compiled.setdefault("applicability", "always")
    compiled.setdefault("requiredness", "UNSPECIFIED")
    compiled.setdefault(
        "locator",
        {
            "strategy": "template-conditioned-edge-proposal",
            "anchor": _DEFAULT_ZONE_ANCHOR.get(zone_id),
        },
    )
    compiled.setdefault(
        "presence_states",
        ["PRESENT", "ABSENT", "NOT_APPLICABLE", "NOT_LOCALIZED", "OCCLUDED", "UNREADABLE"],
    )
    compiled.setdefault("reliability_prior", None)
    return compiled


def normalized_rect(zone: dict[str, Any]) -> list[float]:
    return [float(value) for value in zone["rect"]]


_DEFAULT_ZONE_ANCHOR = {
    "title": "header_band",
    "hp": "header_band",
    "classification": "header_band",
    "owner_mechanic": "header_band",
    "artwork": "artwork_frame",
    "abilities": "body_frame",
    "attacks": "body_frame",
    "attack_costs": "body_frame",
    "damage": "body_frame",
    "weakness": "matchup_band",
    "resistance": "matchup_band",
    "retreat": "matchup_band",
    "set_symbol": "footer_band",
    "collector_number": "footer_band",
    "rarity": "footer_band",
    "illustrator": "footer_band",
    "regulation_edition_promo": "footer_band",
    "copyright_footer": "footer_band",
    "special_layout_markers": "footer_band",
}


def crop_zone(image, zone: dict[str, Any]):
    height, width = image.shape[:2]
    x, y, w, h = (float(value) for value in zone["rect"])
    x0, y0 = max(0, round(x * width)), max(0, round(y * height))
    x1, y1 = min(width, round((x + w) * width)), min(height, round((y + h) * height))
    return image[y0:y1, x0:x1], [x0, y0, x1, y1]
