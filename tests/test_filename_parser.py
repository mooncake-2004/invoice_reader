"""Tests for configured PLMN filename patterns."""

from invoice_reader.services.filename_parser import FilenameParser


def test_extracts_plmn_before_anchor() -> None:
    parser = FilenameParser(["<PLMN>_MACHT"])

    assert parser.parse("FFFFF_MACHT_20261244.pdf") == "FFFFF"


def test_extracts_plmn_after_anchor() -> None:
    parser = FilenameParser(["INV_<PLMN>"])

    assert parser.parse("2026_INV_Ab12Z.pdf") == "Ab12Z"


def test_matches_literal_anchor_without_case_sensitivity() -> None:
    parser = FilenameParser(["<PLMN>_macht"])

    assert parser.parse("AbC12_MACHT_20261244.pdf") == "AbC12"


def test_returns_empty_string_when_no_pattern_matches() -> None:
    parser = FilenameParser(["<PLMN>_MACHT"])

    assert parser.parse("FFFFF_OTHER_20261244.pdf") == ""


def test_uses_first_matching_pattern() -> None:
    parser = FilenameParser(["<PLMN>_MACHT", "INV_<PLMN>"])

    assert parser.parse("AAAA_MACHT_INV_BBBB.pdf") == "AAAA"
