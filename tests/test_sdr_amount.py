"""Tests for locale-independent SDR amount parsing."""

from decimal import Decimal

import pytest

from invoice_reader.application.sdr_amount import normalize_sdr_amount, parse_sdr_amount


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("0,23", "0.23"),
        ("321.45", "321.45"),
        ("1.234,56", "1234.56"),
        ("1,234.56", "1234.56"),
        ("1 234,50", "1234.50"),
    ],
)
def test_normalizes_supported_sdr_formats(raw_value: str, expected: str) -> None:
    assert normalize_sdr_amount(raw_value) == expected
    assert parse_sdr_amount(raw_value) == Decimal(expected)


@pytest.mark.parametrize("raw_value", ["", "SDR 0,23", "1,2,3"])
def test_rejects_invalid_sdr_formats(raw_value: str) -> None:
    with pytest.raises(ValueError):
        parse_sdr_amount(raw_value)
