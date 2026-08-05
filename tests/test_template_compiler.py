"""Tests for PLMN stored in a newly compiled template."""

from invoice_reader.templates.template_compiler import TemplateCompiler
from invoice_reader.templates.template_models import FIELD_NAMES, create_template_field


def test_records_plmn_in_template() -> None:
    fields = {
        field_name: create_template_field(field_name, 1, (0.1, 0.2, 0.3, 0.4))
        for field_name in FIELD_NAMES
    }

    template = TemplateCompiler(0.02).compile(
        "Example",
        "Company",
        "ABCDE",
        [],
        [],
        fields,
        (595.0, 842.0),
        "sample-hash",
    )

    assert template.plmn == "ABCDE"
