import json
from pathlib import Path

from jsonschema import Draft202012Validator

from ptcg.evidence import ContentAddressedArtifactStore
from ptcg.localization import initialize_zone_observations
from ptcg.run_control import RunManifest
from ptcg.template_registry import TemplateRegistry
from ptcg.vision import classify_template_hierarchy


ROOT = Path(__file__).parents[1]


def _validate(schema_name: str, instance):
    schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(instance)


def test_new_runtime_contract_instances_validate(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PTCG_PROJECT_ROOT", str(tmp_path))
    artifact = ContentAddressedArtifactStore(tmp_path / "artifacts").put_bytes(
        b"fixture", role="contract-fixture"
    )
    _validate("artifact-ref.schema.json", artifact)

    manifest = RunManifest.build(
        source_sha256="a" * 64,
        corpus_sha256="b" * 64,
        template_registry_sha256="c" * 64,
        pipeline_version="fixture",
        ocr_provider="none",
        schema_versions={"fixture": "v1"},
        configuration={"offline": True},
    )
    _validate("run-manifest.schema.json", manifest.payload)

    registry = TemplateRegistry(ROOT / "templates")
    classification = classify_template_hierarchy(
        {"yellow_border_fraction": 0.8, "green_face_fraction": 0.1, "aspect_ratio": 0.716},
        {"script": "Unknown", "japanese_character_fraction": 0.0},
        registry,
    )
    _validate("template-classification.schema.json", classification)

    template = registry.resolve(classification["selected_for_localization"])
    observations = initialize_zone_observations(
        template,
        [[0, 0], [629, 0], [629, 879], [0, 879]],
        {"glare_fraction": 0.0, "laplacian_variance": 100.0},
    )
    for observation in observations.values():
        _validate("zone-observation.schema.json", observation)
