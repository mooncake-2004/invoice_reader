"""Compile manual field locations into a new or updated template."""

from datetime import datetime, timezone
from uuid import uuid4

from invoice_reader.templates.template_models import FIELD_NAMES, InvoiceTemplate, TemplateField


class TemplateCompiler:
    """Build a local template from the current PDF and field selections."""

    def __init__(self, page_size_tolerance: float) -> None:
        self._page_size_tolerance = page_size_tolerance

    def compile(
        self,
        display_name: str,
        company: str,
        plmn: str,
        required_keywords: list[str],
        optional_keywords: list[str],
        fields: dict[str, TemplateField],
        page_size_points: tuple[float, float],
        sample_pdf_hash: str,
        existing_template: InvoiceTemplate | None = None,
    ) -> InvoiceTemplate:
        """Return a template after validating its minimum required inputs."""
        if not display_name:
            raise ValueError("请填写模板名。")
        if not company:
            raise ValueError("请填写公司名。")
        if not plmn:
            raise ValueError("文件名未解析出 PLMN，不能保存模板。")
        if set(fields) != set(FIELD_NAMES):
            raise ValueError("请框选四个字段后再保存模板。")

        now = datetime.now(timezone.utc).isoformat()
        return InvoiceTemplate(
            schema_version=1 if existing_template is None else existing_template.schema_version,
            template_id=uuid4().hex if existing_template is None else existing_template.template_id,
            display_name=display_name,
            company=company,
            plmn=plmn,
            required_keywords=required_keywords,
            optional_keywords=optional_keywords,
            page_size_points=page_size_points,
            page_size_tolerance=(
                self._page_size_tolerance
                if existing_template is None
                else existing_template.page_size_tolerance
            ),
            fields=fields,
            created_at=now if existing_template is None else existing_template.created_at,
            updated_at=now,
            sample_pdf_hash=sample_pdf_hash,
        )
