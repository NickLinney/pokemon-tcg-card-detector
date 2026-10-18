from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import verify_run
from .service import analyze_page_request
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
    else:  # pragma: no cover - argparse prevents this branch
        raise AssertionError("unreachable command")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
