"""Compile the four manually selected field locations into a template."""

from datetime import datetime, timezone
from uuid import uuid4

from invoice_reader.templates.template_models import FIELD_NAMES, InvoiceTemplate, TemplateField


class TemplateCompiler:
    """Build a new local template from the current PDF and field selections."""

    def __init__(self, page_size_tolerance: float) -> None:
        self._page_size_tolerance = page_size_tolerance

    def compile(
        self,
        display_name: str,
        company: str,
        required_keywords: list[str],
        optional_keywords: list[str],
        fields: dict[str, TemplateField],
        page_size_points: tuple[float, float],
        sample_pdf_hash: str,
    ) -> InvoiceTemplate:
        """Return a template after validating its minimum required inputs."""
        if not display_name:
            raise ValueError("请填写模板名。")
        if not company:
            raise ValueError("请填写公司名。")
        if not required_keywords:
            raise ValueError("请至少填写一个必需关键词。")
        if set(fields) != set(FIELD_NAMES):
            raise ValueError("请框选四个字段后再保存模板。")

        now = datetime.now(timezone.utc).isoformat()
        return InvoiceTemplate(
            schema_version=1,
            template_id=uuid4().hex,
            display_name=display_name,
            company=company,
            required_keywords=required_keywords,
            optional_keywords=optional_keywords,
            page_size_points=page_size_points,
            page_size_tolerance=self._page_size_tolerance,
            fields=fields,
            created_at=now,
            updated_at=now,
            sample_pdf_hash=sample_pdf_hash,
        )
