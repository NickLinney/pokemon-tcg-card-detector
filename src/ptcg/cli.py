from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import verify_run
from .service import analyze_page_request
from .reviews import ReviewStore
from .evaluation import GroundTruthRegistry
from .tcgdex import ingest_tcgdex, verify_database
from .template_registry import TemplateRegistry
from .version import CANONICAL_VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ptcg")
    parser.add_argument("--version", action="version", version=f"%(prog)s {CANONICAL_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    corpus = subparsers.add_parser("corpus")
    corpus_commands = corpus.add_subparsers(dest="corpus_command", required=True)
    ingest = corpus_commands.add_parser("ingest")
    ingest.add_argument("tcgdex_path", type=Path)
    ingest.add_argument("--database", type=Path, required=True)
    ingest.add_argument("--manifest", type=Path, required=True)
    verify = corpus_commands.add_parser("verify")
    verify.add_argument("database", type=Path)

    evidence = subparsers.add_parser("evidence")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_verify = evidence_commands.add_parser("verify")
    evidence_verify.add_argument("run_directory", type=Path)

    template = subparsers.add_parser("template")
    template_commands = template.add_subparsers(dest="template_command", required=True)
    validate = template_commands.add_parser("validate")
    validate.add_argument("--root", type=Path, default=_repository_root() / "templates")

    page = subparsers.add_parser("page")
    page_commands = page.add_subparsers(dest="page_command", required=True)
    analyze = page_commands.add_parser("analyze")
    analyze.add_argument("image", type=Path)
    analyze.add_argument("--database", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)
    analyze.add_argument("--templates", type=Path, default=_repository_root() / "templates")
    analyze.add_argument("--ocr", choices=("easyocr", "none"), default="easyocr")
    analyze.add_argument("--download-ocr-models", action="store_true")
    analyze.add_argument("--idempotency-key")
    analyze.add_argument("--collection-id", default="sample")
    analyze.add_argument("--binder-id", default="sample")
    analyze.add_argument("--page-id", default="page-1")
    analyze.add_argument("--source-captured-at")

    review = subparsers.add_parser("review")
    review_commands = review.add_subparsers(dest="review_command", required=True)
    review_list = review_commands.add_parser("list")
    review_list.add_argument("--database", type=Path, required=True)
    review_list.add_argument("--state", default="REQUIRED")
    review_list.add_argument("--limit", type=int, default=25)
    review_list.add_argument("--offset", type=int, default=0)
    review_show = review_commands.add_parser("show")
    review_show.add_argument("review_id")
    review_show.add_argument("--database", type=Path, required=True)
    review_decide = review_commands.add_parser("decide")
    review_decide.add_argument("review_id")
    review_decide.add_argument("--database", type=Path, required=True)
    review_decide.add_argument("--actor", required=True)
    review_decide.add_argument("--authority-scope", required=True)
    review_decide.add_argument(
        "--action",
        required=True,
        choices=(
            "SELECT_CANDIDATE",
            "MANUAL_ASSERTION",
            "REJECT_ALL",
            "CORRECT_FIELD",
            "REQUEST_RECAPTURE",
            "LEAVE_UNRESOLVED",
        ),
    )
    review_decide.add_argument("--reason", required=True)
    review_decide.add_argument("--evidence-version", required=True)
    review_decide.add_argument("--expected-prior-assertion")
    review_decide.add_argument("--reference-card-id")
    review_decide.add_argument("--printing-assertion-json")
    review_decide.add_argument("--field-correction-json")

    inventory = subparsers.add_parser("inventory")
    inventory_commands = inventory.add_subparsers(dest="inventory_command", required=True)
    inventory_export = inventory_commands.add_parser("export")
    inventory_export.add_argument("collection_id")
    inventory_export.add_argument("--database", type=Path, required=True)
    inventory_export.add_argument("--output", type=Path, required=True)

    evaluate = subparsers.add_parser("evaluate")
    evaluate_commands = evaluate.add_subparsers(dest="evaluate_command", required=True)
    fixture_validate = evaluate_commands.add_parser("fixtures")
    fixture_validate.add_argument("registry", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "corpus" and args.corpus_command == "ingest":
        result = ingest_tcgdex(args.tcgdex_path, args.database, args.manifest)
    elif args.command == "corpus" and args.corpus_command == "verify":
        result = verify_database(args.database)
    elif args.command == "evidence" and args.evidence_command == "verify":
        result = verify_run(args.run_directory)
        if result["status"] != "PASS":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 5
    elif args.command == "template" and args.template_command == "validate":
        registry = TemplateRegistry(args.root)
        findings = registry.validate()
        result = {"template_count": len(registry.ids()), "templates": registry.ids(), "findings": findings}
        result["registry_sha256"] = registry.digest()
        result["coverage"] = registry.coverage()
        if findings:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 1
    elif args.command == "page" and args.page_command == "analyze":
        result = analyze_page_request(
            args.image,
            args.database,
            args.templates,
            args.output,
            ocr_mode=args.ocr,
            download_ocr_models=args.download_ocr_models,
            idempotency_key=args.idempotency_key,
            context={
                "collection_id": args.collection_id,
                "binder_id": args.binder_id,
                "page_id": args.page_id,
                "source_captured_at": args.source_captured_at,
            },
        )
    elif args.command == "review" and args.review_command == "list":
        result = ReviewStore(args.database).list(
            state=args.state.upper(), limit=args.limit, offset=args.offset
        )
    elif args.command == "review" and args.review_command == "show":
        result = ReviewStore(args.database).get(args.review_id)
    elif args.command == "review" and args.review_command == "decide":
        result = ReviewStore(args.database).append_disposition(
            args.review_id,
            actor_id=args.actor,
            authority_scope=args.authority_scope,
            payload={
                "action": args.action,
                "reason": args.reason,
                "evidence_version": args.evidence_version,
                "expected_prior_assertion": args.expected_prior_assertion,
                "identity_assertion": (
                    {"reference_card_id": args.reference_card_id}
                    if args.reference_card_id
                    else None
                ),
                "printing_assertion": _json_argument(args.printing_assertion_json),
                "field_correction": _json_argument(args.field_correction_json),
            },
        )
    elif args.command == "inventory" and args.inventory_command == "export":
        paths = ReviewStore(args.database).export_effective_inventory(
            args.collection_id, args.output
        )
        result = {key: str(value) for key, value in paths.items()}
    elif args.command == "evaluate" and args.evaluate_command == "fixtures":
        result = GroundTruthRegistry.load(args.registry).validate()
        if result["status"] != "PASS":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 6
    else:  # pragma: no cover - argparse prevents this branch
        raise AssertionError("unreachable command")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _json_argument(value: str | None):
    if value is None:
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("JSON argument must be an object")
    return parsed


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
