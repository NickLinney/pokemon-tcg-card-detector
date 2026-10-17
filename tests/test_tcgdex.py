from pathlib import Path

import pytest

from ptcg.tcgdex import parse_card, verify_database


PROJECT = Path(__file__).resolve().parents[2]
CORPUS = PROJECT / "corpus-sources" / "tcgdex-cards-database-v2.48.0"
DATABASE = PROJECT / ".local" / "corpus" / "tcgdex-v2.48.0-r3.sqlite3"


@pytest.mark.skipif(not CORPUS.exists(), reason="pinned local corpus is not present")
def test_parse_vs_card_preserves_source_and_identifiers():
    card = parse_card(CORPUS / "data-asia/VS/VS1/001.ts", CORPUS)
    assert card.source_card_id == "VS1-001"
    assert card.canonical_reference_id == "tcgdex:data-asia:VS1-001"
    assert card.names["ja"]
    assert card.hp == 60
    assert len(card.source_payload_hash) == 64
    assert "name" in card.mapped_fields


@pytest.mark.skipif(not DATABASE.exists(), reason="compiled local corpus is not present")
def test_compiled_corpus_integrity():
    result = verify_database(DATABASE)
    assert result["integrity_check"] == "ok"
    assert result["card_count"] == 42055
    assert result["import_error_count"] == 0
