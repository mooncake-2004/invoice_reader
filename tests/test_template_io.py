"""Tests for portable template JSON files."""

import json
from dataclasses import replace

import pytest

from invoice_reader.templates.template_io import TemplateFileError, TemplateIo
from invoice_reader.templates.template_models import InvoiceTemplate, create_template_field
from invoice_reader.ui.main_window import MainWindow


def _template() -> InvoiceTemplate:
    return InvoiceTemplate(
        schema_version=1,
        template_id="ABCDE",
        display_name="ABCDE",
        company="ABCDE",
        plmn="ABCDE",
        required_keywords=["Invoice"],
        optional_keywords=["SDR"],
        page_size_points=(595.0, 842.0),
        page_size_tolerance=0.02,
        fields={"invoice_no": create_template_field("invoice_no", 1, (0.1, 0.2, 0.3, 0.4))},
        created_at="2026-08-07T00:00:00+00:00",
        updated_at="2026-08-07T00:00:00+00:00",
        sample_pdf_hash="sample",
    )


def test_exports_and_imports_template_data(tmp_path) -> None:
    exchange_path = tmp_path / "templates.json"
    TemplateIo().export_templates(str(exchange_path), [_template()])

    imported = TemplateIo().import_templates(str(exchange_path))

    assert imported[0].to_mapping() == _template().to_mapping()


def test_import_ignores_unknown_template_fields(tmp_path) -> None:
    exchange_path = tmp_path / "templates.json"
    payload = {"format_version": 1, "templates": [_template().to_mapping() | {"future_setting": "ignored"}]}
    exchange_path.write_text(json.dumps(payload), encoding="utf-8")

    assert TemplateIo().import_templates(str(exchange_path))[0].plmn == "ABCDE"


def test_rejects_invalid_exchange_file(tmp_path) -> None:
    exchange_path = tmp_path / "templates.json"
    exchange_path.write_text("not json", encoding="utf-8")

    with pytest.raises(TemplateFileError):
        TemplateIo().import_templates(str(exchange_path))


def test_keep_both_renames_an_imported_conflicting_template() -> None:
    window = object.__new__(MainWindow)
    window._templates = [_template()]
    imported = replace(_template(), optional_keywords=["new"])

    assert MainWindow._template_conflicts(window, imported) == [_template()]
    renamed = MainWindow._renamed_import_template(window, imported)

    assert renamed.template_id != imported.template_id
    assert renamed.display_name == "ABCDE (导入)"
